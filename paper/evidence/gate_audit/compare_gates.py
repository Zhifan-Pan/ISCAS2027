"""Reproducible CPU-only retrospective gate replay with frozen G4/B/N banks.

The sole counterfactual is the outer gate. Each gate is max-pooled across
windows before selecting the entire recording's B or N+R output. Counts use
the existing complete-reference multiwindow lookup, never summed window WER.
"""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
import argparse, csv, hashlib, json, sys
from pathlib import Path
import numpy as np
LANGS=['ar','fa','pl','tr','it']; SEEDS=[101,202,303]
GATES={'CR_utf8_gt_2p4':('cr_utf8',2.4),'word_r43_gt_0':('r43',0.),'CR_token_ids_gt_1p35':('cr_token_ids',1.35)}
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()
def csvwrite(p,rows):
    with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();r,o=a.repo.resolve(),a.output.resolve();o.mkdir(exist_ok=True,parents=True)
    sys.path.insert(0,str(r/'experiments/acceptors/tools'));from objective_engine import choose
    from evaluate_acceptors import score_selected
    inputs={};rows=[];langrows=[];invariants=[]
    def load(path):
        path=Path(path);inputs[str(path.relative_to(r))]=sha(path)
        if path.suffix=='.npz':
            with np.load(path,allow_pickle=False) as z:return {k:z[k] for k in z.files}
        return json.loads(path.read_text())
    model=load(r/'reproduction/config/SELECTORS.json')['checkpoints'];prior=load(r/'reproduction/analyses/helpful_recovery_accounting.json')
    for ds in ['FLEURS','CV27']:
        for seed in SEEDS:
            p=load(r/f'experiments/acceptors/inputs/{ds}_{seed}.npz');f=load(o/f'{ds}_{seed}_gate_features.npz');np.testing.assert_array_equal(f['ids'],p['ids']);np.testing.assert_array_equal(f['window_owner'],p['window_owner']);np.testing.assert_array_equal(f['window_index'],p['window_index'])
            beta=model[str(seed)]['F']['raw_beta'];bp=choose(p['x'],p['k_beam'],[0,1,2,3],beta);npick=choose(p['x'],p['k'],[0,1,2,3],beta)
            np.testing.assert_array_equal(bp,p['B_pick']);np.testing.assert_array_equal(npick,p['N_pick']);bc=score_selected(p,bp);nc=score_selected(p,npick);np.testing.assert_array_equal(bc,p['B']);np.testing.assert_array_equal(nc,p['N'])
            lang=p['lang'];den=np.array([bc[lang==l,3].sum() for l in range(5)]);w=20./den[lang];be=bc[:,:3].sum(1);ne=nc[:,:3].sum(1);positive=np.maximum(be-ne,0);beneficial=positive>0
            macro=lambda c:float(np.mean([100*c[lang==l,:3].sum()/c[lang==l,3].sum() for l in range(5)]))
            saved={'ids':p['ids'],'lang':lang,'window_owner':p['window_owner'],'B':bc,'N':nc}
            for name,(feature,threshold) in GATES.items():
                wf=f[feature]>threshold;flags=np.zeros(len(lang),bool);np.logical_or.at(flags,p['window_owner'],wf)
                pick=np.where(flags[p['window_owner']],npick,bp);c=score_selected(p,pick);np.testing.assert_array_equal(c,np.where(flags[:,None],nc,bc));np.testing.assert_array_equal(c[:,3],bc[:,3])
                if name=='CR_utf8_gt_2p4':np.testing.assert_array_equal(flags,p['flags']);np.testing.assert_array_equal(c,p['S'])
                posgain=float(w@positive);posloss=float(w@(positive*(~flags)));retention=100*(1-posloss/posgain)
                row={'dataset':ds,'checkpoint':seed,'gate':name,'recordings':len(lang),'windows':len(bp),'triggered_recordings':int(flags.sum()),'acquired_windows':int(flags[p['window_owner']].sum()),'locally_triggered_windows':int(wf.sum()),'calls_pct':float(100*flags.mean()),'macro_B_WER':macro(bc),'macro_N_WER':macro(nc),'macro_S_WER':macro(c),'gain_from_B_pp':macro(bc)-macro(c),'positive_gain_pp':posgain,'positive_gain_lost_pp':posloss,'positive_gain_retention_pct':retention,'beneficial_instances':int(beneficial.sum()),'beneficial_instances_retained':int((beneficial&flags).sum()),'positive_edits':int(positive.sum()),'positive_edits_retained':int(positive[flags].sum()),'overlap_original_triggered_recordings':int((flags&p['flags']).sum()),'new_vs_original_triggered_recordings':int((flags&~p['flags']).sum()),'missed_original_triggered_recordings':int((~flags&p['flags']).sum())};rows.append(row)
                for l,language in enumerate(LANGS):
                    ix=lang==l;v=c[ix].sum(0);b=bc[ix].sum(0);n=nc[ix].sum(0)
                    langrows.append({'dataset':ds,'checkpoint':seed,'gate':name,'language':language,'recordings':int(ix.sum()),'triggered_recordings':int(flags[ix].sum()),'calls_pct':float(100*flags[ix].mean()),'B_S':int(b[0]),'B_D':int(b[1]),'B_I':int(b[2]),'N_S':int(n[0]),'N_D':int(n[1]),'N_I':int(n[2]),'S':int(v[0]),'D':int(v[1]),'I':int(v[2]),'reference_words':int(v[3]),'B_WER':float(100*b[:3].sum()/b[3]),'N_WER':float(100*n[:3].sum()/n[3]),'S_WER':float(100*v[:3].sum()/v[3]),'positive_edits':int(positive[ix].sum()),'positive_edits_retained':int(positive[ix&flags].sum()),'beneficial_instances':int(beneficial[ix].sum()),'beneficial_instances_retained':int((beneficial&flags)[ix].sum())})
                saved[name+'_flags']=flags;saved[name+'_counts']=c
            np.savez_compressed(o/f'{ds}_{seed}_replay.npz',**saved)
            invariants.append({'dataset':ds,'checkpoint':seed,'B_N_fixed_G4_picks_and_counts_exact':True,'original_gate_flags_and_counts_exact':True,'all_three_gates_recording_score_lookup_exact':True,'reference_denominators_equal':True})
    means=[]
    for ds in ['FLEURS','CV27']:
        for gate in GATES:
            group=[v for v in rows if v['dataset']==ds and v['gate']==gate];g=float(np.mean([v['positive_gain_pp'] for v in group]));lost=float(np.mean([v['positive_gain_lost_pp'] for v in group]));n=sum(v['recordings'] for v in group);tr=sum(v['triggered_recordings'] for v in group)
            mean={'dataset':ds,'gate':gate,'seed_recordings':n,'triggered_seed_recordings':tr,'calls_pct':100*tr/n,'macro_B_WER':float(np.mean([v['macro_B_WER'] for v in group])),'macro_N_WER':float(np.mean([v['macro_N_WER'] for v in group])),'macro_S_WER':float(np.mean([v['macro_S_WER'] for v in group])),'gain_from_B_pp':float(np.mean([v['gain_from_B_pp'] for v in group])),'positive_gain_pp':g,'positive_gain_lost_pp':lost,'positive_gain_retention_pct':100*(1-lost/g),'beneficial_instances':sum(v['beneficial_instances'] for v in group),'beneficial_instances_retained':sum(v['beneficial_instances_retained'] for v in group),'positive_edits':sum(v['positive_edits'] for v in group),'positive_edits_retained':sum(v['positive_edits_retained'] for v in group),'acquired_windows':sum(v['acquired_windows'] for v in group),'total_windows':sum(v['windows'] for v in group)};means.append(mean)
            if gate=='CR_utf8_gt_2p4':
                old=prior['summary'][ds];assert abs(mean['macro_S_WER']-old['macro_SplusR_WER'])<1e-12;assert abs(mean['macro_N_WER']-old['macro_NplusR_WER'])<1e-12;assert abs(mean['positive_gain_retention_pct']-100*old['macro_weighted_beneficial_edit_retention'])<1e-12
    csvwrite(o/'PER_SEED.csv',rows);csvwrite(o/'PER_LANGUAGE_SEED.csv',langrows);csvwrite(o/'SUMMARY.csv',means)
    result={'summary':means,'scope':'Retrospective counterfactual gate replay on fixed cached TEST banks, fixed G4 and unchanged candidate draws. No GPU or new decoding, no confirmation or runtime claim. Token gate is compression-only screening of the original beam; it does not reproduce the combined HF retry or no-speech policy.','protocol':{'original':'max_window CR_UTF8(text)>2.4','word':'max_window r4,3(top_beam)>0, original normalized word feature','alternative':'max_window CR_token_ids(top_beam generated tokens including natural EOS)>1.35, 2-byte little-endian HF 4.57.6 compression','aggregation':'recording flags are OR across windows; selected output is N+R on every window if triggered, B otherwise','WER':'Within-language sum(S+D+I)/sum(reference words), equal 5-language mean, then equal 3-checkpoint mean.','calls':'All triggered seed-recordings / all seed-recordings; acquired windows reported separately.','retention':'1 - mean_seed mean_language sum_positive (E_B-E_N)*1{gate off}/N_language divided by mean_seed mean_language sum_positive(E_B-E_N)/N_language; not pooled edits and not average per-seed retention.','test_tuning':'No threshold fit or search; fixed requested 2.4, 0 and HF 1.35. Exploratory post hoc evaluation.'},'invariants':invariants,'input_sha256':inputs,'script_sha256':sha(__file__)}
    (o/'RESULT.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps(means,indent=2),flush=True)
if __name__=='__main__':main()
