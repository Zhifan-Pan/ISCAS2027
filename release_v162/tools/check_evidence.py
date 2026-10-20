"""V162 bounded, descriptive checks on immutable candidate and timing artifacts.

No new decoding, bootstrap, timing or confirmation. Full joined-recording SDIN
tables are used for FLEURS, including every two-window combination.
"""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from objective_engine import choose

R = Path(__file__).resolve().parents[1]
W = R.parent
A = W / 'final_decision_return/reviewer_artifact/acceptors'
SEEDS = [101, 202, 303]
LANG = ['ar', 'fa', 'pl', 'tr', 'it']

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def load(p):
    return json.loads(Path(p).read_text())

def arrays(p):
    with np.load(p, allow_pickle=False) as z:
        return {k: z[k].copy() for k in z.files}

def save(p, obj):
    Path(p).write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')

def csvout(p, rows):
    with Path(p).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def macro(c, lang):
    return float(np.mean([100*c[lang == j, :3].sum()/c[lang == j, 3].sum() for j in range(5)]))

def score(p, picks):
    assert picks.shape == p['k'].shape and ((picks >= 0) & (picks < p['k'])).all()
    start = p['offsets'][:-1]
    c = p['single_counts'][start, picks[start]].copy()
    for j, row in enumerate(p['multi_rows']):
        lo, hi = p['offsets'][row:row+2]
        assert hi-lo == 2
        a, b = picks[lo:hi]
        c[row] = p['multi_counts'][j, a, b]
    np.testing.assert_array_equal(c[:, 3], p['B'][:, 3])
    return c

def digest(p, d, picks):
    start = p['offsets'][:-1]
    out = d['text_digest'][start, picks[start]].copy()
    for j, row in enumerate(p['multi_rows']):
        lo, hi = p['offsets'][row:row+2]
        a, b = picks[lo:hi]
        out[row] = d['multi_text_digest'][j, a, b]
    return out

def model(family, seed):
    if family == 'G4':
        return list(range(4)), load(A/'inputs/G4_LOCK.json')[str(seed)]['raw_beta']
    if family == 'HWR4':
        p = W/f'revision_v152/models/HWR4_{seed}.json'
    elif family == 'H4plusE':
        p = R/f'models/H4plusE_{seed}.json'
    else:
        p = A/f'models/{family}_{seed}.json'
    m = load(p)
    return m['columns'], m['raw_beta']

def candidates(with_refit):
    out = R/'analysis'/('refit_evaluation' if with_refit else 'candidate_audit')
    out.mkdir(exist_ok=False); (out/'counts').mkdir(); (out/'picks').mkdir()
    rows, per, audit, receipt, record_rows, empty = [], [], [], [], [], []
    families = ['H4plusE'] if with_refit else ['G4', 'H4', 'HR4', 'H3', 'HWR4']
    for ds in ['FLEURS', 'CV27']:
        for seed in SEEDS:
            pf = A/f'inputs/{ds}_{seed}.npz'; df = W/f'revision_v152/private/{ds}_{seed}_diagnostics.npz'
            p, d = arrays(pf), arrays(df)
            rec = load(W/f'revision_v152/analysis/input_export/{ds}_{seed}.json')
            assert sha(pf) == rec['public_input'] and sha(df) == rec['output_sha256']
            for k in ['ids', 'k', 'k_beam']:
                np.testing.assert_array_equal(p[k], d[k])
            z = p['flags'][p['window_owner']]
            cols, beta = model('G4', seed)
            bp = choose(p['x'], p['k_beam'], cols, beta); npick = choose(p['x'], p['k'], cols, beta)
            np.testing.assert_array_equal(bp, p['B_pick']); np.testing.assert_array_equal(npick, p['N_pick'])
            sp = np.where(z, npick, bp); dp = np.where(z, p['hf_index'], bp)
            for name, pick in [('B',bp),('N',npick),('S',sp),('Direct',dp)]:
                np.testing.assert_array_equal(score(p,pick), p[name])
            g4delta = p['B'][:, :3]-p['S'][:, :3]
            sf, bf = digest(p,d,sp), digest(p,d,bp)
            allc, allp = {}, {}
            for family in families:
                x = p['x']
                if family == 'H4plusE':
                    e = d['raw_empty'].astype(float)
                    x = np.concatenate([x, (e-e[:,:1])[:,:,None]], 2)
                cols, beta = model(family, seed)
                b = choose(x, p['k_beam'], cols, beta); n = choose(x, p['k'], cols, beta)
                s = np.where(z,n,b); t = np.where(z,n,bp)
                c = {k:score(p,pk) for k,pk in [('B',b),('N',n),('S',s),('T',t)]}
                for name, cc in c.items():
                    rows.append(dict(corpus=ds,checkpoint=seed,acceptor=family,policy=name,WER=macro(cc,p['lang'])))
                    for j,ll in enumerate(LANG):
                        v = cc[p['lang']==j].sum(0)
                        per.append(dict(corpus=ds,checkpoint=seed,acceptor=family,policy=name,language=ll,S=int(v[0]),D=int(v[1]),I=int(v[2]),N=int(v[3]),WER=float(100*v[:3].sum()/v[3])))
                bs, ss = digest(p,d,b), digest(p,d,s)
                delta = c['B'][:,:3]-c['S'][:,:3]
                np.testing.assert_array_equal(c['S'][~p['flags']],c['B'][~p['flags']])
                np.testing.assert_array_equal(bs[~p['flags']],ss[~p['flags']])
                ar = dict(corpus=ds,checkpoint=seed,acceptor=family,triggered_recordings=int(p['flags'].sum()),triggered_windows=int(z.sum()),hf_picks_on_acquired_windows=int((s[z]==p['hf_index'][z]).sum()),B_WER=macro(c['B'],p['lang']),S_WER=macro(c['S'],p['lang']),gain_pp=macro(c['B'],p['lang'])-macro(c['S'],p['lang']),different_gain_SDIs_vs_G4=int(np.any(delta!=g4delta,axis=1).sum()),different_gain_edits_vs_G4=int((delta.sum(1)!=g4delta.sum(1)).sum()),different_triggered_S_texts_vs_G4=int((ss[p['flags']]!=sf[p['flags']]).sum()),different_triggered_B_texts_vs_G4=int((bs[p['flags']]!=bf[p['flags']]).sum()),S_Direct_WER_difference=macro(c['S'],p['lang'])-macro(p['Direct'],p['lang']))
                audit.append(ar)
                if ds == 'FLEURS':
                    for i in np.flatnonzero(p['flags']):
                        record_rows.append(dict(checkpoint=seed,acceptor=family,id=str(p['ids'][i]),language=LANG[p['lang'][i]],B_edits=int(c['B'][i,:3].sum()),S_edits=int(c['S'][i,:3].sum()),Direct_edits=int(p['Direct'][i,:3].sum()),S_equals_Direct_text=bool(ss[i]==digest(p,d,dp)[i]),delta_edits=int(delta[i].sum()),gain_SDIs=delta[i].tolist()))
                allc.update({family+'_'+k:v for k,v in c.items()})
                allp.update({family+'_'+k:v for k,v in [('B',b),('N',n),('S',s),('T',t)]})
            if not with_refit:
                valid = np.arange(6)[None,:]<p['k'][:,None]
                inb = np.arange(6)[None,:]<p['k_beam'][:,None]
                empt = d['raw_empty'] & valid
                accepted = z & d['raw_empty'][np.arange(len(sp)),sp]
                rev = np.where(accepted,bp,sp)
                gp = arrays(W/f'revision_v159/analysis/candidate_controls/picks/{ds}_{seed}.npz')['G4_guard_S']
                gc = score(p,gp); rc = score(p,rev)
                empty.append(dict(corpus=ds,checkpoint=seed,raw_empty_original_bank=int((empt&inb).sum()),raw_empty_expanded_bank=int(empt.sum()),raw_empty_HF=int(d['raw_empty'][np.arange(len(sp)),p['hf_index']].sum()),accepted_empty_instances=int(accepted.sum()),accepted_empties_equal_hf=bool(np.all(sp[accepted]==p['hf_index'][accepted])),guard_revert_identical_picks=bool(np.array_equal(gp,rev)),guard_revert_identical_texts=bool(np.array_equal(digest(p,d,gp),digest(p,d,rev))),guard_revert_identical_SDIN=bool(np.array_equal(gc,rc)),guard_WER=macro(gc,p['lang']),removed_gain_pp=macro(rc,p['lang'])-macro(p['S'],p['lang']),remaining_gain_pp=macro(p['B'],p['lang'])-macro(rc,p['lang']),acceptance_delta_SDIN=(p['S']-rc).sum(0).tolist(),accepted_recording_ids=[str(x) for x in p['ids'][np.unique(p['window_owner'][accepted])]]))
            np.savez_compressed(out/f'counts/{ds}_{seed}.npz',ids=p['ids'],lang=p['lang'],**allc)
            np.savez_compressed(out/f'picks/{ds}_{seed}.npz',ids=p['ids'],**allp)
            receipt.append(dict(corpus=ds,seed=seed,inputs_sha256=sha(pf),diagnostics_sha256=sha(df)))
            print('checked',ds,seed,flush=True)
    means = [dict(corpus=ds,acceptor=f,policy=k,WER=float(np.mean([v['WER'] for v in rows if v['corpus']==ds and v['acceptor']==f and v['policy']==k]))) for ds in ['FLEURS','CV27'] for f in families for k in ['B','N','S','T']]
    csvout(out/'policies.csv',rows);csvout(out/'per_language_SDIN.csv',per);csvout(out/'selection_audit.csv',audit)
    csvout(out/'FLEURS_triggered_records.csv',record_rows)
    save(out/'RESULT.json',dict(scope='retrospective descriptive; no new intervals or confirmation',means=means,checks=audit,empty=empty,receipts=receipt))

def costs():
    out=R/'analysis/cost_audit';out.mkdir(exist_ok=False)
    src=W/'live_cost_v153_20261019/results/COST_RESULTS.json';d=load(src);rows=[]
    for ds,v in d['datasets'].items():
        m={k:q['weighted_mean_ms'] for k,q in v['policies'].items()}
        # Runtime calls the Direct path SDirect.
        rows.append(dict(corpus=ds,B_minus_Raw_ms=m['B']-m['RawTop1'],N_minus_B_ms=m['NplusR']-m['B'],S_minus_B_ms=m['SplusR']-m['B'],incremental_overhead_saving_pct=100*(m['NplusR']-m['SplusR'])/(m['NplusR']-m['B'])))
    csvout(out/'within_study_B_policy_contrasts.csv',rows)
    covsrc=W/'revision_v159/analysis/cost_scope/trigger_coverage.csv'
    with covsrc.open() as f:cov=list(csv.DictReader(f))
    for row in cov:
        row['outside_census_pct']=100*int(row['triggers_outside_base_census'])/int(row['population'])
        row['outside_census_not_sampled']=int(row['triggers_outside_base_census'])-int(row['sampled_outside_triggers'])
    csvout(out/'trigger_coverage.csv',cov)
    profiles=[]
    for p in sorted((W/'live_cost_v153_20261019/profile/round0').glob('*.json')):
        q=load(p); profiles.append({'path':str(p.relative_to(W)),'sha256':sha(p)})
    save(out/'RESULT.json',dict(within_study_B=rows,cost_source_sha256=sha(src),coverage_source_sha256=sha(covsrc),profile_files=profiles,interpretation='Population-weighted policy contrasts, not isolated stage times. The 25-recording profile is unweighted and not conditioned on multi-candidate banks.',millisecond_bound='UNSUPPORTED: missing-event probability alone cannot bound unmeasured latency',new_GPU_measurements=False))
    print(rows,flush=True)

if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['candidates','refit','costs']);args=ap.parse_args()
    if args.phase=='costs':costs()
    else:candidates(args.phase=='refit')
