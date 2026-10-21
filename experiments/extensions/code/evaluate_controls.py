"""Locked same-HF MBR, HWR4, H3Direct and window diagnostics; CPU only."""
from common import *
from objective_engine import choose
from audit_existing import reconstruct
import argparse

def mbr(p,d,bank,temperature=None):
    k=p[bank];valid=np.arange(6)[None,:]<k[:,None]
    if temperature is None:
        mass=valid/k[:,None]
    else:
        mass=np.zeros(valid.shape,float)
        multi=k>1;single=~multi;mass[single,0]=1
        a=p['raw_features'][multi,:,0];nt=d['body_tokens'][multi];v=valid[multi]
        assert np.isfinite(a[v]).all() and (nt[v]>=0).all()
        s=np.where(v,a*nt/temperature,-np.inf)
        s-=s.max(1)[:,None];t=np.exp(s);t/=t.sum(1)[:,None];mass[multi]=t
    dist=d['distance'];pair=valid[:,:,None]&valid[:,None,:]
    assert (dist[pair]>=0).all()
    risk=np.sum(np.where(pair,dist,0)*mass[:,None,:],axis=2)
    risk[~valid]=np.inf
    pick=np.argmin(risk,axis=1)
    assert ((pick>=0)&(pick<k)).all()
    return pick

def dev():
    out=R/'analysis/E02_DEV';out.mkdir(exist_ok=False);plan=load(R/'protocols/LOCKED_PLAN.json');models={};rows=[]
    for seed in SEEDS:
        p=arrays(A/f'acceptors/inputs/DEV_{seed}.npz');d=arrays(R/f'numeric_inputs/DEV_{seed}_diagnostics.npz')
        np.testing.assert_array_equal(p['ids'],d['ids']);np.testing.assert_array_equal(p['k'],d['k'])
        temperatures=plan['E02']['temperatures'];loss=[]
        for temp in temperatures:
            pick=mbr(p,d,'k',temp);value=macro(p['counts'][np.arange(len(pick)),pick],p['lang']);loss.append(value)
            rows.append(dict(checkpoint=seed,temperature=temp,full_HF_DEV_WER=value))
        best=min(range(len(loss)),key=lambda i:(loss[i],-temperatures[i]))
        uniform=mbr(p,d,'k')
        models[str(seed)]=dict(temperature=temperatures[best],DEV_WER=loss[best],uniform_DEV_WER=macro(p['counts'][np.arange(len(uniform)),uniform],p['lang']),input_sha256=sha(A/f'acceptors/inputs/DEV_{seed}.npz'),diagnostics_sha256=sha(R/f'numeric_inputs/DEV_{seed}_diagnostics.npz'))
    writecsv(out/'temperature_grid.csv',rows)
    save(R/'models/MBR_LOCK.json',dict(frozen_utc=utc(),models=models,plan_sha256=sha(R/'protocols/LOCKED_PLAN.json'),scope='DEV-only temperature selection; primary uniform; all candidates retained'))
    print(json.dumps({'phase':'E02_DEV','models':models}),flush=True)

def evaluate():
    lock=load(R/'models/MBR_LOCK.json');hwlock=load(R/'models/HWR4_LOCK.json')
    for name,h in hwlock['models'].items():assert sha(R/'models'/name)==h
    out=R/'analysis/controls';out.mkdir(exist_ok=False);rows=[];langrows=[];parts=[];checks=[]
    (out/'counts').mkdir();(out/'picks').mkdir()
    for ds in ['FLEURS','CV27']:
        for seed in SEEDS:
            p=arrays(A/f'acceptors/inputs/{ds}_{seed}.npz');d=arrays(R/f'numeric_inputs/{ds}_{seed}_diagnostics.npz')
            np.testing.assert_array_equal(p['ids'],d['ids']);np.testing.assert_array_equal(p['k'],d['k'])
            cs,pk,beta=reconstruct(p,seed);allc={};allp={};z=p['flags'][p['window_owner']]
            for fam,temp in [('MBR_uniform',None),('MBR_body',lock['models'][str(seed)]['temperature']),('HWR4',None)]:
                if fam=='HWR4':
                    b=np.array(load(R/f'models/HWR4_{seed}.json')['raw_beta'])
                    bp=choose(p['x'],p['k_beam'],list(range(4)),b);npick=choose(p['x'],p['k'],list(range(4)),b)
                else:bp=mbr(p,d,'k_beam',temp);npick=mbr(p,d,'k',temp)
                picks={'B':bp,'N':npick,'S':np.where(z,npick,bp),'T':np.where(z,npick,pk['B'])}
                counts={f'{name}_{fam}':score(p,v) for name,v in picks.items()};allc.update(counts)
                allp.update({f'{name}_{fam}':v for name,v in picks.items()})
                bcount=counts[f'B_{fam}'];ncount=counts[f'N_{fam}'];scount=counts[f'S_{fam}'];tcount=counts[f'T_{fam}']
                np.testing.assert_array_equal(scount,np.where(p['flags'][:,None],ncount,bcount))
                np.testing.assert_array_equal(tcount,np.where(p['flags'][:,None],ncount,cs['B']))
                checks.append(dict(corpus=ds,checkpoint=seed,acceptor=fam,S_T_reconstruction=True))
            original=arrays(A/f'acceptors/counts/PICKS_{ds}_{seed}.npz')
            h3d=np.where(z,p['hf_index'],original['B_H3']);allc['H3Direct']=score(p,h3d);allp['H3Direct']=h3d
            window_flag=d['cr_window']>2.4;windowpick=np.where(window_flag,pk['N'],pk['B'])
            allc['G4_window_CR']=score(p,windowpick);allp['G4_window_CR']=windowpick
            np.testing.assert_array_equal(allc['G4_window_CR'][np.diff(p['offsets'])==1],cs['S'][np.diff(p['offsets'])==1])
            delta=allc['G4_window_CR'][:,:3].sum(1)-cs['S'][:,:3].sum(1);w=macro_weights(cs['B'],p['lang'])
            parts.append(dict(corpus=ds,checkpoint=seed,two_window_recordings=len(p['multi_rows']),changed_recordings=int(np.any(allc['G4_window_CR']!=cs['S'],axis=1).sum()),window_minus_recording_CR_pp=float(w@delta),recording_CR_acquired_windows=int(z.sum()),window_CR_acquired_windows=int(window_flag.sum()),latency='NOT_MEASURED'))
            r,l=policy_rows(ds,seed,p,allc);rows+=r;langrows+=l
            for row in r:
                fam=row['policy'].split('_',1)[-1];base=allc.get(f'B_{fam}')
                row['gain_vs_own_B_pp']=macro(base,p['lang'])-row['WER'] if base is not None else None
            np.savez_compressed(out/f'counts/{ds}_{seed}.npz',ids=p['ids'],lang=p['lang'],**allc)
            np.savez_compressed(out/f'picks/{ds}_{seed}.npz',ids=p['ids'],**allp)
            print(json.dumps({'evaluated':ds,'seed':seed,'policies':len(allc)}),flush=True)
    writecsv(out/'policies.csv',rows);writecsv(out/'per_language_SDIN.csv',langrows);writecsv(out/'window_diagnostic.csv',parts)
    means=[dict(corpus=ds,policy=name,WER=float(np.mean([r['WER'] for r in rows if r['corpus']==ds and r['policy']==name]))) for ds in ['FLEURS','CV27'] for name in allc]
    save(out/'RESULT.json',dict(means=means,reconstruction_checks=checks,scope='retrospective complete TEST, original full-reference joint two-window counts; no new confirmation or runtime'))

def paired():
    out=R/'analysis/statistics';out.mkdir(exist_ok=False)
    comp=arrays(A/'acceptors/inputs/CV27_COMPONENTS.npz');names=['T_MBR_uniform','T_HWR4'];stack=[];n=None;lang=comp['lang']
    for seed in SEEDS:
        p=arrays(A/f'acceptors/inputs/CV27_{seed}.npz');old=arrays(A/f'acceptors/counts/CV27_{seed}.npz');new=arrays(R/f'analysis/controls/counts/CV27_{seed}.npz')
        for v in [p,new]:np.testing.assert_array_equal(v['ids'],comp['ids']);np.testing.assert_array_equal(v['lang'],lang)
        if n is None:n=p['B'][:,3]
        else:np.testing.assert_array_equal(n,p['B'][:,3])
        stack.append(np.stack([new[name][:,:3].sum(1)-old['T_H4'][:,:3].sum(1) for name in names]))
    effects=np.mean(stack,axis=0);suff=[];point=np.zeros(2)
    for l in range(5):
        ix=lang==l;_,inv=np.unique(comp['components'][ix],return_inverse=True)
        e=np.stack([np.bincount(inv,weights=v[ix]) for v in effects]);den=np.bincount(inv,weights=n[ix]);assert (den>0).all()
        suff.append((e,den));point+=20*e.sum(1)/den.sum()
    cfg=load(R/'protocols/LOCKED_PLAN.json')['statistics'];rng=np.random.default_rng(cfg['rng_seed']);samples=np.zeros((cfg['draws'],2))
    for draw in range(cfg['draws']):
        for e,den in suff:
            take=rng.choice(len(den),len(den),replace=True);samples[draw]+=20*e[:,take].sum(1)/den[take].sum()
    ci=np.quantile(samples,cfg['individual_interval'],axis=0)
    results=[dict(contrast=f'{name} - T_H4',corpus='CV27',difference_pp=float(point[i]),CI_97_5_pp=ci[:,i].tolist(),checkpoint_differences_pp=[float(sum(20*v[i,lang==l].sum()/n[lang==l].sum() for l in range(5))) for v in stack]) for i,name in enumerate(names)]
    save(out/'RESULT.json',dict(contrasts=results,configuration=cfg,components_per_language=[len(x[1]) for x in suff],scope='two prespecified contrasts, Bonferroni family 95%; synchronized checkpoints; conditional on frozen fits'))
    np.savez_compressed(out/'bootstrap_draws.npz',differences=samples)
    print(json.dumps(results),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--phase',required=True,choices=['dev','test','stats']);a=ap.parse_args()
    {'dev':dev,'test':evaluate,'stats':paired}[a.phase]()
