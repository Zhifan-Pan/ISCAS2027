"""Refit frozen R8 gates and recompute their TEST statistics from numerical inputs.

No GPU, network, transcript text, confirmation reuse or parameter search on TEST.
Expected results are read only after the new fits, flags and statistics exist.
"""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
from pathlib import Path
import argparse, csv, datetime, hashlib, json, time
import numpy as np
from hf_gate_math import ridge_fit, predict, select_lambda, calibrated_thresholds
from scientific_core import cross_validate, align_windows, aggregate_verified, macro, paired_interval
from evaluate_budget_matched import mix_counts, matched_flags

LANGS = ['ar', 'fa', 'pl', 'tr', 'it']
SEEDS = [101, 202, 303]

def load(p): return json.loads(p.read_text())
def arrays(p):
    with np.load(p, allow_pickle=False) as z: return dict(z)
def save(p, d): p.write_text(json.dumps(d, indent=2, allow_nan=False) + '\n')
def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def check_counts(a, name):
    assert a.ndim == 2 and a.shape[1] == 4, (name, a.shape)
    assert a.dtype.kind in 'iu' and (a >= 0).all(), name
    assert (a[:, 0] + a[:, 1] <= a[:, 3]).all(), name
def csvwrite(p, rows):
    with p.open('x') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args(); root = args.root.resolve(); out = args.out.resolve()
    assert not out.exists(), 'Use a new output directory; expected inputs are never overwritten.'
    out.mkdir(parents=True)
    started = utc(); start = time.monotonic()
    plan = load(root / 'protocol.json'); qs = plan['quantiles']; alphas = plan['lambda_grid']
    models = {}; losses = []; supports = []; paired_DEV = None
    for seed in SEEDS:
        z = arrays(root / f'inputs/dev/DEV_{seed}.npz')
        n = len(z['ids']); assert n == 58171 and len(set(z['ids'])) == n
        for key in ['B', 'NplusR']: check_counts(z[key], key)
        np.testing.assert_array_equal(z['B'][:,3], z['NplusR'][:,3])
        np.testing.assert_array_equal(z['y'], z['B'][:,:3].sum(1) - z['NplusR'][:,:3].sum(1))
        assert set(z['fold']) == set(range(5))
        # Components must never be split across folds.
        assignment = {}
        for comp, fold in zip(z['components'], z['fold']):
            assert assignment.setdefault(str(comp), int(fold)) == fold
        if paired_DEV is None: paired_DEV = [z[k] for k in ['ids','lang','fold','components']]
        else:
            for a,k in zip(paired_DEV,['ids','lang','fold','components']): np.testing.assert_array_equal(a,z[k])
        assert z['eligible'].sum() == plan['population']['eligible_per_checkpoint'][str(seed)]
        for domain in ['all', 'eligible', 'ineligible']:
            m = np.ones(n,bool) if domain == 'all' else z['eligible'] if domain == 'eligible' else ~z['eligible']
            y = z['y'][m]
            supports.append(dict(seed=seed,domain=domain,recordings=int(m.sum()),
                components=len(np.unique(z['components'][m])), positive=int((y>0).sum()),
                negative=int((y<0).sum()), zero=int((y==0).sum()),net_edit_benefit=int(y.sum())))
        models[str(seed)] = {}
        for gate,d in [('HF12',12),('HF9',9)]:
            x=z['features'][:,:d]
            oof,constant,loss,constant_loss,fold_models = cross_validate(x,z['y'],z['lang'],z['fold'],z['eligible'],alphas)
            best=select_lambda(loss,alphas)
            model=ridge_fit(x,z['y'],z['lang'],z['eligible'],alphas[best])
            score=-predict(x,model)
            model.update(gate=gate,dimensions=d,thresholds=calibrated_thresholds(score,z['eligible'],qs),
                selected_lambda=alphas[best],cv_losses=loss.tolist(),constant_baseline_cv_loss=constant_loss)
            models[str(seed)][gate]=model
            for a,l in zip(alphas,loss): losses.append(dict(checkpoint=seed,gate=gate,lambda_value=a,
                weighted_MSE=float(l),constant_MSE=constant_loss,selected=a==alphas[best]))
            save(out/f'fold_models_{seed}_{gate}.json',fold_models)
    # TEST IO starts only after generated coefficients/thresholds have been saved.
    save(out/'models.json',dict(frozen_utc=utc(),models=models,quantiles=qs,alphas=alphas))
    cp=[]; ctr=[]; eq=[]; pl=[]; deltas=[]; primary_meta=None; recon=[]; flags_checked=0
    for corpus in ['FLEURS','CV27']:
        for seed in SEEDS:
            z=arrays(root/f'inputs/test/SCORES_{corpus}_{seed}.npz')
            old=arrays(root/f'inputs/test/CONTROLS_{corpus}_{seed}.npz')
            win=arrays(root/f'inputs/test/WINDOWS_{corpus}_{seed}.npz')
            b,n,lang=z['B'],z['NplusR'],z['lang']; nr=len(b)
            for key in ['B','NplusR','SplusR']:check_counts(z[key],key)
            for key in ['ids','lang','eligible']:np.testing.assert_array_equal(z[key],old[key])
            np.testing.assert_array_equal(z['cr_matched'],z['cr_original'] & z['eligible'])
            np.testing.assert_array_equal(b[:,3],n[:,3])
            np.testing.assert_array_equal(mix_counts(b,n,z['cr_original']),z['SplusR'])
            index=align_windows(win,z['ids'],lang,z['eligible'])
            cr=mix_counts(b,n,z['cr_matched']); cw=macro(cr,lang)
            recomputed={}
            def describe(gate,flag,view,q):
                counts=mix_counts(b,n,flag)
                return dict(corpus=corpus,checkpoint=seed,policy=gate,view=view,q=q,
                    recordings=nr,calls=int(flag.sum()),calls_percent=100.*float(flag.mean()),
                    macro_WER_percent=macro(counts,lang),delta_vs_CR_matched_pp=macro(counts,lang)-cw)
            for gate in ['HF12','HF9']:
                model=models[str(seed)][gate]
                scores=-predict(win['features'][:,:model['dimensions']],model)
                rs,el,flags=aggregate_verified(scores,win,index,nr,model['thresholds'],qs)
                np.testing.assert_array_equal(el,z['eligible'])
                np.testing.assert_allclose(rs,z[f'{gate}_scores'],rtol=0,atol=1e-12)
                np.testing.assert_array_equal(flags,z[f'{gate}_flags']); flags_checked+=9
                recomputed[gate]=(rs,flags)
                for j,q in enumerate(qs):
                    cp.append(describe(gate,flags[j],'DEV_threshold',str(q)))
                    c=mix_counts(b,n,flags[j])
                    for l,label in enumerate(LANGS):
                        m=lang==l;den=int(b[m,3].sum());wer=100.*c[m,:3].sum()/den
                        pl.append(dict(corpus=corpus,checkpoint=seed,gate=gate,q=str(q),language=label,
                            recordings=int(m.sum()),calls=int(flags[j,m].sum()),
                            calls_percent=100.*float(flags[j,m].mean()),WER_percent=float(wer),
                            delta_vs_CR_matched_pp=float(wer-100.*cr[m,:3].sum()/den)))
            for gate,flag,q in [('B',np.zeros(nr,bool),None),('NplusR',np.ones(nr,bool),None),
                ('CR_original',z['cr_original'],None),('CR_matched',z['cr_matched'],None),
                ('G12_GreedyTrained_HFexecution',old['G12_flags'][1],'0.003'),
                ('gap_DEVcalibrated_HFexecution',old['gap_flags'][1],'0.003')]:
                ctr.append(describe(gate,flag,'frozen_control',q))
            k=int(z['cr_matched'].sum());keys=[f'{corpus}|{LANGS[int(l)]}|{uid}' for l,uid in zip(lang,z['ids'])]
            for gate,score in [('HF12',recomputed['HF12'][0]),('HF9',recomputed['HF9'][0]),
                ('G12_GreedyTrained_HFexecution',old['G12_scores']),('gap_DEVcalibrated_HFexecution',old['gap_scores'])]:
                flags=matched_flags(score,z['eligible'],keys,k,plan['tie_salt'])
                row=describe(gate,flags,'equal_K_retrospective',None);row['K']=k
                assert row['calls']==k;eq.append(row)
            recon.append(dict(corpus=corpus,checkpoint=seed,recordings=nr,original_S_count_mismatches=0,
                windows=len(index),min_any_checks=18,CR_matched_K=k))
            if corpus=='CV27':
                s=mix_counts(b,n,recomputed['HF12'][1][1])
                deltas.append(s[:,:3].sum(1)-cr[:,:3].sum(1))
                meta=(z['ids'],lang,b[:,3],z['cluster'])
                if primary_meta is None:primary_meta=meta
                else:
                    for a,c in zip(primary_meta,meta):np.testing.assert_array_equal(a,c)
    aggregate=[]
    for source in [cp,ctr,eq]:
        for corpus,policy,view,q in dict.fromkeys((r['corpus'],r['policy'],r['view'],r['q']) for r in source):
            rows=[r for r in source if (r['corpus'],r['policy'],r['view'],r['q'])==(corpus,policy,view,q)]
            assert len(rows)==3
            aggregate.append(dict(corpus=corpus,policy=policy,view=view,q=q,
                recordings_per_checkpoint=rows[0]['recordings'],checkpoint_recording_instances=sum(r['recordings'] for r in rows),
                calls=sum(r['calls'] for r in rows),calls_percent=float(np.mean([r['calls_percent'] for r in rows])),
                macro_WER_percent=float(np.mean([r['macro_WER_percent'] for r in rows])),
                delta_vs_CR_matched_pp=float(np.mean([r['delta_vs_CR_matched_pp'] for r in rows]))))
    ids,lang,words,components=primary_meta
    point,ci,draws=paired_interval(np.asarray(deltas),words,lang,components,
        draws=plan['bootstrap_draws'],seed=plan['bootstrap_seed'])
    primary=dict(point_pp=point,CI95_pp=ci.tolist(),draws=plan['bootstrap_draws'],rng_seed=plan['bootstrap_seed'])
    save(out/'results.json',dict(rows=aggregate,primary=primary,reconstruction=recon))
    for name,rows in [('summary.csv',aggregate),('cv_losses.csv',losses),('label_support.csv',supports),
        ('dev_threshold_grid.csv',cp),('matched_K_results.csv',eq),('per_language_hf.csv',pl)]:csvwrite(out/name,rows)
    # Separate post-generation comparisons; no expected outputs are used for fits or ranking.
    expected_models=load(root/'expected/frozen_models.json')['models']
    checked=0
    def compare(a,b,path):
        nonlocal checked
        if isinstance(a,dict):
            assert set(a)==set(b),path
            for k in a:compare(a[k],b[k],path+'/'+k)
        elif isinstance(a,list):
            assert len(a)==len(b),path
            for i,(x,y) in enumerate(zip(a,b)):compare(x,y,path+'/'+str(i))
        elif isinstance(a,(int,float)) and not isinstance(a,bool):
            assert abs(a-b)<1e-10,(path,a,b);checked+=1
        else:assert a==b,(path,a,b)
    compare(models,expected_models,'models')
    expected=load(root/'expected/results.json')
    compare(aggregate,expected['rows'],'summary')
    for key in primary:compare(primary[key],expected['primary'][key],'primary/'+key)
    assert len(cp)==108 and len(eq)==24 and flags_checked==108
    save(out/'verification.json',dict(status='NUMERICAL_REPLAY_MATCH',started_utc=started,ended_utc=utc(),
        elapsed_seconds=time.monotonic()-start,refitted_gates=6,checked_numeric_fields=checked,
        threshold_cells=108,exact_K_cells_new_HF=12,exact_K_cells_inherited_controls=12,
        original_S_reconstructions=6,window_flag_matches=108,component_folds_disjoint=True,
        primary=primary,scope='Numerical reproduction; not new scientific evidence or reference-custody certification.'))
    print(json.dumps(load(out/'verification.json')))

if __name__=='__main__':main()
