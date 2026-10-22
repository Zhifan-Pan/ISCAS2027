"""Recompute language WERs and fixed-model seed diagnostics from frozen caches."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
from pathlib import Path
import argparse, csv, json, sys, hashlib
import numpy as np

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    r,o=a.repo.resolve(),a.output.resolve();o.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(r/'experiments/acceptors/tools'))
    from objective_engine import choose
    from evaluate_acceptors import score_selected
    langs=['ar','fa','pl','tr','it'];seeds=[101,202,303]
    sources={};rows=[];diagnostics=[];betas=[]
    def load(p):
        sources[str(p.relative_to(r))]=hashlib.sha256(p.read_bytes()).hexdigest()
        if p.suffix=='.npz':
            with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
        return json.loads(p.read_text())
    def write(name,data):
        with (o/name).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    g4=load(r/'reproduction/config/SELECTORS.json')['checkpoints']
    for ds in ['FLEURS','CV27']:
        for seed in seeds:
            p=load(r/f'experiments/acceptors/inputs/{ds}_{seed}.npz')
            published=load(r/f'experiments/acceptors/counts/{ds}_{seed}.npz')
            picks=load(r/f'experiments/acceptors/counts/PICKS_{ds}_{seed}.npz')
            rawpick=np.zeros(len(p['k']),int)
            raw=score_selected(p,rawpick)
            for name,c in [('RawTop1',raw),('B',published['B_G4']),('SplusR',published['S_G4'])]:
                for l,lang in enumerate(langs):
                    ix=p['lang']==l;v=c[ix].sum(0)
                    rows.append(dict(dataset=ds,checkpoint=seed,language=lang,policy=name,recordings=int(ix.sum()),triggers=int(p['flags'][ix].sum()),S=int(v[0]),D=int(v[1]),I=int(v[2]),N=int(v[3]),WER=float(100*v[:3].sum()/v[3])))
            if ds!='CV27':continue
            models={'G4':g4[str(seed)]['F']}
            for family in ['H4','HR4','HWR4']:
                folder='extensions' if family=='HWR4' else 'acceptors'
                models[family]=load(r/f'experiments/{folder}/models/{family}_{seed}.json')
            dev=load(r/f'experiments/acceptors/inputs/DEV_{seed}.npz')
            rawdiag=load(r/f'experiments/extensions/numeric_inputs/CV27_{seed}_diagnostics.npz')
            selected={fam:choose(p['x'],p['k'],[0,1,2,3],m['raw_beta']) for fam,m in models.items()}
            np.testing.assert_array_equal(selected['G4'],p['N_pick'])
            np.testing.assert_array_equal(selected['H4'],picks['N_H4'])
            for fam,m in models.items():
                betas.append(dict(checkpoint=seed,acceptor=fam,a=m['raw_beta'][0],p=m['raw_beta'][1],t=m['raw_beta'][2],r=m['raw_beta'][3],penalty=m.get('lambda_value',m.get('lambda',m.get('penalty'))),scale=m['scale'],DEV_triggers=int(dev['flags'].sum())))
            den=np.array([p['single_counts'][p['lang']==l,0,3].sum() for l in range(5)])
            c=p['single_counts'];err=c[:,:,:3].sum(2);idx=np.arange(len(p['k']));macro_w=20/den[p['lang']]
            for label,one,two,scorefam in [('Direct_minus_G4',p['hf_index'],selected['G4'],'G4'),('HWR4_minus_H4',selected['HWR4'],selected['H4'],'HWR4')]:
                delta=err[idx,one]-err[idx,two]
                active=p['flags']&(one!=two)
                digest_diff=rawdiag['text_digest'][idx,one]!=rawdiag['text_digest'][idx,two]
                effect=np.where(p['flags'],delta*macro_w,0)
                details=[]
                for i in np.flatnonzero(active):
                    f1=p['raw_features'][i,one[i]];f2=p['raw_features'][i,two[i]]
                    details.append(dict(id=str(p['ids'][i]),language=langs[p['lang'][i]],candidate_one=int(one[i]),candidate_two=int(two[i]),edit_difference=int(delta[i]),macro_pp=float(effect[i]),raw_one=f1.tolist(),raw_two=f2.tolist(),score_contributions_one_minus_two={f:((f1-f2)*np.array(m['raw_beta'])).tolist() for f,m in models.items()},distinct_normalized_text=bool(digest_diff[i]),raw_CR=float(rawdiag['cr_window'][i])))
                details.sort(key=lambda x:abs(x['macro_pp']),reverse=True)
                diagnostics.append(dict(seed=seed,contrast=label,DEV_triggers=int(dev['flags'].sum()),TEST_triggers=int(p['flags'].sum()),different_picks=int(active.sum()),distinct_texts=int((active&digest_diff).sum()),wins=int((active&(delta<0)).sum()),losses=int((active&(delta>0)).sum()),net_pp=float(effect.sum()),per_language_pp={lang:float(effect[p['lang']==l].sum()) for l,lang in enumerate(langs)},candidates=details))
    write('PER_LANGUAGE_SEED.csv',rows)
    means=[]
    for ds in ['FLEURS','CV27']:
        for lang in langs:
            def mean(policy):return float(np.mean([v['WER'] for v in rows if v['dataset']==ds and v['language']==lang and v['policy']==policy]))
            sample=[v for v in rows if v['dataset']==ds and v['language']==lang and v['policy']=='B']
            means.append(dict(dataset=ds,language=lang,RawTop1_WER=mean('RawTop1'),B_WER=mean('B'),SplusR_WER=mean('SplusR'),Gain_pp=mean('B')-mean('SplusR'),Calls_pct=100*sum(v['triggers'] for v in sample)/sum(v['recordings'] for v in sample)))
    write('PER_LANGUAGE_MEANS.csv',means)
    write('FITTED_WEIGHTS.csv',betas)
    (o/'CHECKPOINT_DIAGNOSTICS.json').write_text(json.dumps(diagnostics,indent=2)+'\n')
    (o/'INPUT_SHA256.json').write_text(json.dumps(sources,indent=2)+'\n')
    # Independently compare every B/S per-language edit count against the
    # existing published evidence CSV, not just its rounded WER.
    archived=list(csv.DictReader((r/'paper/evidence/language_seed_SDIN.csv').open()))
    checks=0
    for row in rows:
        if row['policy']=='RawTop1':continue
        old=next(v for v in archived if all(str(row[k])==v[k] for k in ['dataset','checkpoint','language','policy']))
        assert all(row[k]==int(old[k]) for k in ['S','D','I','N'])
        checks+=1
    print(json.dumps(dict(language_count_checks=checks,means=means,diagnostics=[{k:v for k,v in d.items() if k!='candidates'} for d in diagnostics]),indent=2))

if __name__=='__main__':main()
