"""Independent arithmetic/identity checks for the published numeric gate audit."""
import argparse, csv, hashlib, json
from pathlib import Path
import numpy as np

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);a=ap.parse_args();r=a.repo.resolve();o=r/'paper/evidence/gate_audit';report=json.loads((o/'RESULT.json').read_text());checks=0
    def check(x):
        nonlocal checks
        assert x;checks+=1
    for p,h in report['input_sha256'].items():check(sha(r/p)==h)
    check(report['script_sha256']==sha(o/'compare_gates.py'))
    language=list(csv.DictReader((o/'PER_LANGUAGE_SEED.csv').open()));seedrows=list(csv.DictReader((o/'PER_SEED.csv').open()));summary=list(csv.DictReader((o/'SUMMARY.csv').open()))
    for ds in ['FLEURS','CV27']:
        for seed in [101,202,303]:
            with np.load(o/f'{ds}_{seed}_replay.npz',allow_pickle=False) as p,np.load(o/f'{ds}_{seed}_gate_features.npz',allow_pickle=False) as f:
                be=p['B'][:,:3].sum(1);ne=p['N'][:,:3].sum(1);positive=np.maximum(be-ne,0)
                for gate,feature,threshold in [('CR_utf8_gt_2p4','cr_utf8',2.4),('word_r43_gt_0','r43',0.),('CR_token_ids_gt_1p35','cr_token_ids',1.35)]:
                    # Independently reduce by record index rather than selected-candidate replay.
                    expected=np.bincount(p['window_owner'],weights=(f[feature]>threshold).astype(int),minlength=len(p['ids']))>0
                    flags=p[gate+'_flags'];c=p[gate+'_counts'];check(np.array_equal(flags,expected));check(np.array_equal(c[flags],p['N'][flags]));check(np.array_equal(c[~flags],p['B'][~flags]))
                    wer=[];gain=[];loss=[]
                    for l,lang in enumerate(['ar','fa','pl','tr','it']):
                        ix=p['lang']==l;row=next(v for v in language if v['dataset']==ds and int(v['checkpoint'])==seed and v['gate']==gate and v['language']==lang);n=c[ix,3].sum();v=c[ix].sum(0)
                        check([int(row[k]) for k in ['S','D','I','reference_words']]==v.tolist());check(int(row['triggered_recordings'])==int(flags[ix].sum()));check(int(row['positive_edits_retained'])==int(positive[ix&flags].sum()))
                        wer.append(100*v[:3].sum()/n);gain.append(100*positive[ix].sum()/n);loss.append(100*positive[ix&~flags].sum()/n)
                    row=next(v for v in seedrows if v['dataset']==ds and int(v['checkpoint'])==seed and v['gate']==gate)
                    check(abs(float(row['macro_S_WER'])-sum(wer)/5)<1e-12);check(abs(float(row['positive_gain_pp'])-sum(gain)/5)<1e-12);check(abs(float(row['positive_gain_lost_pp'])-sum(loss)/5)<1e-12);check(abs(float(row['calls_pct'])-100*flags.sum()/len(flags))<1e-12)
        for gate in ['CR_utf8_gt_2p4','word_r43_gt_0','CR_token_ids_gt_1p35']:
            group=[v for v in seedrows if v['dataset']==ds and v['gate']==gate];row=next(v for v in summary if v['dataset']==ds and v['gate']==gate);g=sum(float(v['positive_gain_pp']) for v in group);lost=sum(float(v['positive_gain_lost_pp']) for v in group)
            check(abs(float(row['positive_gain_retention_pct'])-100*(1-lost/g))<1e-12);check(abs(float(row['macro_S_WER'])-sum(float(v['macro_S_WER']) for v in group)/3)<1e-12)
    result={'checks_passed':checks,'scope':'Independent row-level route, integer counts, denominators, mean WER, macro positive-gain ratio, and input/script hashes.'};(o/'VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
