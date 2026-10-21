"""Full TEST policy evaluation and the two fixed paired component contrasts.

Consumes numeric candidate exports with complete-recording multiwindow
alignment lookup tables. It never sums window edit counts.
"""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
from pathlib import Path
import argparse,json,csv,time
import numpy as np
from fit_acceptor import save,sha,utc,macro
from objective_engine import choose

LANGS=['ar','fa','pl','tr','it'];SEEDS=[101,202,303];FAMILIES=['G4','H4','HR4','H3']
def arrays(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k].copy() for k in z.files}
def score_selected(p,pick):
    offsets=p['offsets'];assert len(pick)==len(p['k'])
    assert ((pick>=0)&(pick<p['k'])).all()
    c=p['single_counts'][offsets[:-1],pick[offsets[:-1]]].copy()
    for j,row in enumerate(p['multi_rows']):
        assert offsets[row+1]-offsets[row]==2
        a,b=pick[offsets[row]:offsets[row+1]];c[row]=p['multi_counts'][j,a,b]
    return c
def writecsv(p,rows):
    with Path(p).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def run(root,data_root):
    started=utc();plan=json.loads((root/'prerefit_plan.json').read_text())
    lock=json.loads((root/'models/MODEL_LOCK.json').read_text());assert len(lock['models'])==9
    for name,h in lock['models'].items():assert sha(root/'models'/name)==h
    assert not (root/'results/policy_summary.csv').exists()
    g4=json.loads((data_root/'G4_LOCK.json').read_text())
    rows=[];perlang=[];allcounts={};pickhashes={};inputhashes={}
    for ds in ['FLEURS','CV27']:
        for seed in SEEDS:
            path=data_root/f'{ds}_{seed}.npz';p=arrays(path);inputhashes[path.name]=sha(path)
            n=len(p['ids']);flags=p['flags'];out={};picks={}
            for family in FAMILIES:
                m=g4[str(seed)] if family=='G4' else json.loads((root/'models'/f'{family}_{seed}.json').read_text())
                cols=[0,1,2,3] if family=='G4' else m['columns'];beta=np.asarray(m['raw_beta'])
                bp=choose(p['x'],p['k_beam'],cols,beta);npick=choose(p['x'],p['k'],cols,beta)
                bc=score_selected(p,bp);nc=score_selected(p,npick)
                out['B_'+family]=bc;out['N_'+family]=nc;out['S_'+family]=np.where(flags[:,None],nc,bc)
                picks['B_'+family]=bp;picks['N_'+family]=npick
                picks['S_'+family]=np.where(flags[p['window_owner']],npick,bp)
                if family!='G4':
                    out['T_'+family]=np.where(flags[:,None],nc,out['B_G4'])
                    picks['T_'+family]=np.where(flags[p['window_owner']],npick,picks['B_G4'])
            out['Direct']=p['Direct']
            picks['Direct']=np.where(flags[p['window_owner']],p['hf_index'],picks['B_G4'])
            np.testing.assert_array_equal(score_selected(p,picks['Direct']),out['Direct'])
            for name,field in [('B_G4','B'),('N_G4','N'),('S_G4','S')]:np.testing.assert_array_equal(out[name],p[field])
            assert len(out)==16
            for name,c in out.items():
                assert c.dtype.kind in 'iu' and (c>=0).all() and (c[:,0]+c[:,1]<=c[:,3]).all()
                np.testing.assert_array_equal(c[:,3],p['B'][:,3])
                fam=name.split('_')[-1] if name!='Direct' else 'G4'
                gain=macro(out['B_'+fam],p['lang'])-macro(c,p['lang']) if not name.startswith('T_') else macro(out['B_G4'],p['lang'])-macro(c,p['lang'])
                rows.append({'corpus':ds,'checkpoint':seed,'policy':name,'recordings':n,'macro_WER':macro(c,p['lang']),'gain_from_own_B_pp':gain if not name.startswith('T_') else '', 'gain_from_G4_B_pp':gain if name.startswith('T_') or name=='Direct' else ''})
                for l,language in enumerate(LANGS):
                    v=c[p['lang']==l].sum(0)
                    perlang.append({'corpus':ds,'checkpoint':seed,'policy':name,'language':language,'S':int(v[0]),'D':int(v[1]),'I':int(v[2]),'N':int(v[3]),'WER':100*int(v[:3].sum())/int(v[3])})
            target=root/'counts'/f'{ds}_{seed}.npz'
            np.savez_compressed(target,ids=p['ids'],lang=p['lang'],flags=flags,**out)
            pp=root/'counts'/f'PICKS_{ds}_{seed}.npz';np.savez_compressed(pp,window_owner=p['window_owner'],window_index=p['window_index'],**picks)
            allcounts[ds,seed]=(p['ids'],p['lang'],out);pickhashes[pp.name]=sha(pp)
    assert len(rows)==96 and len(perlang)==480
    writecsv(root/'results/policy_summary.csv',rows);writecsv(root/'results/per_language_SDIN.csv',perlang)
    means=[]
    for ds in ['FLEURS','CV27']:
        for name in allcounts[ds,101][2]:
            vals=[next(v['macro_WER'] for v in rows if v['corpus']==ds and v['checkpoint']==s and v['policy']==name) for s in SEEDS]
            means.append({'corpus':ds,'policy':name,'macro_WER':float(np.mean(vals)),'checkpoint_WER':vals})
    save(root/'results/three_checkpoint_means.json',means)
    component=arrays(data_root/'CV27_COMPONENTS.npz')
    contrasts=[('C1','T_HR4','T_H4'),('C2','S_H3','S_H4')]
    langs=component['lang'];diff=[];N=None;points=[]
    for s in SEEDS:
        ids,ll,c=allcounts['CV27',s];np.testing.assert_array_equal(ids,component['ids']);np.testing.assert_array_equal(ll,langs)
        if N is None:N=c['B_G4'][:,3]
        else:np.testing.assert_array_equal(N,c['B_G4'][:,3])
        diff.append(np.stack([c[a][:,:3].sum(1)-c[b][:,:3].sum(1) for _,a,b in contrasts],axis=-1))
        points.append([macro(c[a],ll)-macro(c[b],ll) for _,a,b in contrasts])
    # Averaging checkpoint edit differences before resampling is algebraically
    # identical to applying the same component draw to each checkpoint.
    delta=np.mean(diff,axis=0);sufficient=[];ng=[]
    for l in range(5):
        ix=langs==l;_,g=np.unique(component['components'][ix],return_inverse=True);ng.append(int(g.max()+1))
        e=np.column_stack([np.bincount(g,weights=delta[ix,j]) for j in range(2)])
        den=np.bincount(g,weights=N[ix]);assert (den>0).all();sufficient.append((e,den))
    stat=plan['statistics'];rng=np.random.default_rng(stat['rng_seed']);draws=np.zeros((stat['draws'],2))
    for b in range(stat['draws']):
        for e,den in sufficient:
            take=rng.choice(len(den),len(den),replace=True);draws[b]+=20*e[take].sum(0)/den[take].sum()
    intervals={name:np.quantile(draws,q,axis=0).T for name,q in stat['intervals'].items()}
    comp=[]
    for j,(name,a,b) in enumerate(contrasts):
        comp.append({'id':name,'corpus':'CV27','difference':a+' - '+b,'mean_pp':float(np.mean(points,axis=0)[j]),'checkpoint_pp':[float(p[j]) for p in points],**{name:val[j].tolist() for name,val in intervals.items()},'negative_favors':a})
    save(root/'results/primary_comparisons.json',{'comparisons':comp,'method':stat,'components_by_language':dict(zip(LANGS,ng)),'environment_scope':'Conditional on fixed fits and original source draws; no new confirmation.'})
    np.savez_compressed(root/'results/bootstrap_draws.npz',draws=draws)
    save(root/'results/EVALUATION_RECEIPT.json',{'started_utc':started,'finished_utc':utc(),'cells':len(rows),'per_language_rows':len(perlang),'full_corpora':True,'G4_B_N_S_Direct_exact_all_six_panels':True,'multiwindow_scoring':'private complete-reference lookup after selected text concatenation, not window-edit addition','plan_sha256':sha(root/'prerefit_plan.json'),'model_lock_sha256':sha(root/'models/MODEL_LOCK.json'),'inputs':inputhashes,'pick_files':pickhashes,'new_inference':False,'new_confirmation':False})
    print(json.dumps({'cells':len(rows),'primary_comparisons':comp}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--data-root',type=Path,required=True);a=p.parse_args();run(a.root.resolve(),a.data_root.resolve())
