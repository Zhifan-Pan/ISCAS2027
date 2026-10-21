#!/usr/bin/env python3
"""Read-only V146 evidence audit. No inference, fitting, bootstrap or rating.
Uses the submitted full recording-level counts, not reported rounded means.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, platform
from pathlib import Path
import numpy as np

SEEDS = (101, 202, 303)
POLS = ('B', 'Native', 'NplusR', 'SplusR')

def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1048576), b''):h.update(b)
    return h.hexdigest()

def validate_counts(c):
    if set(c) != {'S','D','I','N'}: raise ValueError('Expected S,D,I,N')
    if any(type(v) is not int or v<0 for v in c.values()):raise ValueError('Nonnegative integer counts required')
    if c['S']+c['D']>c['N']:raise ValueError('S+D exceeds N')

def err(c): return c['S']+c['D']+c['I']

def mwer(rows, policy):
    langs=sorted({r['lang'] for r in rows})
    vals=[]
    for lang in langs:
        rs=[r for r in rows if r['lang']==lang]
        den=sum(r[policy]['N'] for r in rs)
        if den<=0:raise ValueError('Zero language denominator')
        vals.append(100*sum(err(r[policy]) for r in rs)/den)
    return sum(vals)/len(vals)

def run(root: Path):
    root=root.resolve(); used={}
    def use(rel):
        p=root/rel
        if not p.is_file():raise FileNotFoundError(p)
        used[rel]=sha(p);return p
    rs=[json.loads(s) for s in use('confirmation/panel_scores_v2.jsonl').read_text().splitlines() if s.strip()]
    keys=[(r['lang'],r['id'],r['seed']) for r in rs]
    if len(set(keys))!=len(keys):raise ValueError('Duplicate paired instance')
    if {r['seed'] for r in rs}!=set(SEEDS):raise ValueError('Unexpected checkpoints')
    idsets=[]; per_cp=[]
    for r in rs:
        for p in POLS:validate_counts(r[p])
        if len({r[p]['N'] for p in POLS})!=1:raise ValueError('Policy reference mismatch')
        if type(r['outer_trigger']) is not bool:raise ValueError('Invalid gate flag')
        want=r['NplusR'] if r['outer_trigger'] else r['B']
        if r['SplusR']!=want:raise ValueError('S+R reconstruction failed')
    for s in SEEDS:
        part=[r for r in rs if r['seed']==s]
        idsets.append({(r['lang'],r['id']) for r in part})
        w={p:mwer(part,p) for p in POLS}
        raw=sum(err(r['B'])-err(r['SplusR']) for r in part)
        per_cp.append({'checkpoint':s,'recordings':len(part),'WER_percent':w,
                       'gain_B_minus_S_pp':w['B']-w['SplusR'],
                       'net_raw_edits_reduced':raw,
                       'triggered_instances':sum(r['outer_trigger'] for r in part),
                       'beneficial_instances':sum(err(r['SplusR'])<err(r['B']) for r in part),
                       'harmful_instances':sum(err(r['SplusR'])>err(r['B']) for r in part)})
    if any(x!=idsets[0] for x in idsets[1:]):raise ValueError('Incomplete checkpoint pairing')
    byid=collections.defaultdict(list)
    for r in rs:byid[(r['lang'],r['id'])].append(r)
    for group in byid.values():
        if len({r['B']['N'] for r in group})!=1:raise ValueError('Reference changes across checkpoints')
        if len({r['speaker_key'] for r in group})!=1:raise ValueError('Group identity changes across checkpoints')
    rawtot=sum(v['net_raw_edits_reduced'] for v in per_cp)
    gaintot=sum(v['gain_B_minus_S_pp'] for v in per_cp)
    for v in per_cp:
        v['share_of_net_raw_edits_percent']=100*v['net_raw_edits_reduced']/rawtot if rawtot else None
        v['share_of_summed_macro_gains_percent']=100*v['gain_B_minus_S_pp']/gaintot if gaintot else None
    good=[r for r in rs if err(r['SplusR'])<err(r['B'])]
    good_recordings={(r['lang'],r['id']) for r in good}
    good_speakers={(r['lang'],r['speaker_key']) for r in good}
    c={'instances':len(rs),'recordings':len(idsets[0]),'per_checkpoint':per_cp,
       'positive_instances':len(good),'positive_distinct_recordings':len(good_recordings),
       'positive_speaker_groups':len(good_speakers),
       'B_minus_S_macro_gain_pp':gaintot/len(SEEDS),
       'NplusR_SplusR_equal_vectors':all(r['NplusR']==r['SplusR'] for r in rs),
       'scope':'Descriptive reuse of original panel, not a new confirmation or interval.'}
    language_effects=[]
    for lang in sorted({r['lang'] for r in rs}):
        vals=[]
        for seed in SEEDS:
            part=[r for r in rs if r['lang']==lang and r['seed']==seed]
            vals.append(mwer(part,'B')-mwer(part,'SplusR'))
        avg=sum(vals)/len(vals)
        language_effects.append({'language':lang,'per_checkpoint_gain_pp':dict(zip(map(str,SEEDS),vals)),
            'mean_gain_pp':avg,'share_of_five_language_macro_gain_percent':100*(avg/5)/(gaintot/3)})
    c['per_language_gain']=language_effects
    gate=[]; dev=[]; schemas=[]
    for s in SEEDS:
        rel=f'r8/inputs/dev/DEV_{s}.npz'
        with np.load(use(rel),allow_pickle=False) as z:
            b=z['B']; n=z['NplusR'];y=z['y'];l=z['lang'];eligible=z['eligible']
            np.testing.assert_array_equal(y,b[:,:3].sum(1)-n[:,:3].sum(1))
            np.testing.assert_array_equal(b[:,3],n[:,3])
            counts={'checkpoint':s,'recordings':len(y),'components':len(set(zip(l.tolist(),z['components'].tolist()))),
                    'positive_labels':int((y>0).sum()),'negative_labels':int((y<0).sum()),'zero_labels':int((y==0).sum()),
                    'eligible_positive_labels':int(((y>0)&eligible).sum())}
            dev.append(counts)
            schemas.append({'path':rel,'fields':{k:{'shape':list(z[k].shape),'dtype':str(z[k].dtype)} for k in z.files},
             'candidate_level_acceptor_features_present':False,
             'reason':'features is recording/window x 12 acquisition features; no per-candidate (a,p,t,r) array, bank offsets or complete candidate scores.'})
        for corpus in ('FLEURS','CV27'):
            rel=f'r8/inputs/test/SCORES_{corpus}_{s}.npz'
            with np.load(use(rel),allow_pickle=False) as z:
                # Published, fixed q=0.003 is the second row; checked against model lock grid below.
                f=z['HF12_flags'][1]
                gate.append({'corpus':corpus,'checkpoint':s,'q':0.003,'recordings':len(f),
                   'HF12_calls':int(f.sum()),'CR_original_calls':int(z['cr_original'].sum()),
                   'CR_matched_calls':int(z['cr_matched'].sum()),
                   'HF12_calls_percent':100*float(f.mean())})
    lock=json.loads(use('r8/expected/frozen_models.json').read_text())
    if [float(x) for x in lock['quantiles']][1]!=0.003:raise ValueError('q row interpretation mismatch')
    fle=[v for v in gate if v['corpus']=='FLEURS'];fle_total=sum(v['HF12_calls'] for v in fle)
    return {'scope':'Read-only descriptive audit of submitted counts and frozen flags. No new fit, timing, inference, bootstrap, reference access audit or acceptance guarantee.',
      'environment':{'python':platform.python_version(),'numpy':np.__version__},
      'confirmation':c,'HF_DEV_label_information':dev,'HF12_fixed_q_calls':gate,
      'FLEURS_HF12_101_fraction_of_calls_percent':100*fle[0]['HF12_calls']/fle_total if fle_total else None,
      'candidate_cache_schema':schemas,
      'not_established':'This audit does not establish whether the author workspace contains complete candidate-level exports.',
      'input_sha256':used}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--artifact-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    root=a.artifact_root.resolve();out=a.output.resolve()
    if out==root or root in out.parents:raise SystemExit('Output must be outside the input tree')
    if out.exists():raise SystemExit('Refusing to overwrite output')
    result=run(root);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'confirmation':result['confirmation'],'HF12_fixed_q_calls':result['HF12_fixed_q_calls'],
      'HF_DEV_label_information':result['HF_DEV_label_information']},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
