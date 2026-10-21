"""CPU-only utilities for the fixed retrospective acceptor study."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
from pathlib import Path
import datetime, hashlib, importlib.util, json, math
from collections import Counter
import numpy as np

R=Path(__file__).resolve().parents[1]
W=R.parent
P=Path(os.environ['ISCAS_AUTHOR_PROJECT_ROOT'])
A=P/'artifacts/iscas_repetition_robustness'
V=A/'20261014_v146_matched_recovery'
F=A/'20261014_v150_core_value_closure'
R8=W/'review_round_8'
LANGS=['ar','fa','pl','tr','it']
SEEDS=[101,202,303]
COLS=[0,10,2,4]  # Checked against the original SELECTOR_LOCK, not inferred.
WER_PATH=P/'ASR_v2_CV27_run_20260919/submission_closeout_20260924/reproduction/portable/vendor/wer_rules_v3.py'
spec=importlib.util.spec_from_file_location('acceptor_study_wer',WER_PATH)
wer=importlib.util.module_from_spec(spec);spec.loader.exec_module(wer)
def load(p): return json.loads(Path(p).read_text())
def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def key(s): return hashlib.sha256(str(s).encode()).hexdigest()
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()
def save(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_name(p.name+'.tmp');t.write_text(json.dumps(d,indent=2,ensure_ascii=False,allow_nan=False)+'\n');t.replace(p)
def arrays(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k].copy() for k in z.files}
def repetition(text,lang):
    words=wer.words(text,lang);grams=[tuple(words[i:i+4]) for i in range(max(0,len(words)-3))];freq=Counter(grams)
    return sum(freq[g]>=3 for g in grams)/max(1,len(grams))
def raw4(c,pll,lang):
    """Unknown neural values remain NaN, never synthetic zero raw scores."""
    out=np.full(4,np.nan);nt=-1;pt=-1
    if c.get('clean_logp') is not None and c.get('body_mask') is not None:
        lp=np.asarray(c['clean_logp'],float);mask=np.asarray(c['body_mask'],bool)
        assert len(lp)==len(mask)==len(c['token_ids'])
        body=lp[mask];nt=len(body);out[0]=body.mean() if len(body) else 0.;out[2]=math.log1p(nt)
    if pll is not None:
        out[1]=float(pll['pll']);pt=int(pll.get('target_count',pll.get('ntokens',-1)))
    out[3]=repetition(c['text'],lang)
    return out,nt,pt
def counts(reference,text,lang):
    d=wer.score(reference,text,lang);a=np.array([d[k] for k in ['S','D','I','N']],dtype=np.int64)
    assert (a>=0).all() and a[0]+a[1]<=a[3]
    return a
def macro(c,lang):
    assert set(np.unique(lang))==set(range(5))
    return float(np.mean([100*c[lang==l,:3].sum()/c[lang==l,3].sum() for l in range(5)]))
