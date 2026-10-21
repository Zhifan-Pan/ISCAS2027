"""V152 CPU analyses. Reads frozen inputs; never runs model inference."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
from pathlib import Path
import json, hashlib, datetime, csv, sys
import numpy as np
R=Path(__file__).resolve().parents[1]
W=R.parent
A=W
P=W/'external_inputs_not_distributed'
OLD=W/'external_inputs_not_distributed'
LANGS=['ar','fa','pl','tr','it']
SEEDS=[101,202,303]
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def load(p):return json.loads(Path(p).read_text())
def arrays(p,keys=None):
    with np.load(p,allow_pickle=False) as z:return {k:z[k].copy() for k in (z.files if keys is None else keys)}
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()
def key(s):return hashlib.sha256(str(s).encode()).hexdigest()
def save(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def writecsv(p,rows):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def macro(c,lang):
    assert set(np.unique(lang))==set(range(5))
    return float(np.mean([100*c[lang==l,:3].sum()/c[lang==l,3].sum() for l in range(5)]))
def score(p,pick):
    assert len(pick)==len(p['k']) and ((pick>=0)&(pick<p['k'])).all()
    start=p['offsets'][:-1]
    out=p['single_counts'][start,pick[start]].copy()
    for j,i in enumerate(p['multi_rows']):
        assert p['offsets'][i+1]-p['offsets'][i]==2
        a,b=pick[p['offsets'][i]:p['offsets'][i+1]]
        out[i]=p['multi_counts'][j,a,b]
    return out
def point_parts(p,c,base):
    delta=base[:,:3].sum(1)-c[:,:3].sum(1)
    weights=macro_weights(base,p['lang'])
    return dict(gain_pp=float(weights@delta),wins=int((delta>0).sum()),ties=int((delta==0).sum()),losses=int((delta<0).sum()))
def macro_weights(counts,lang):
    den=np.array([counts[lang==l,3].sum() for l in range(5)])
    assert (den>0).all()
    return (20/den)[lang]
def policy_rows(ds,seed,p,policies):
    rows=[];per=[]
    for name,c in policies.items():
        np.testing.assert_array_equal(c[:,3],p['B'][:,3])
        rows.append(dict(corpus=ds,checkpoint=seed,policy=name,WER=macro(c,p['lang']),**point_parts(p,c,p['B'])))
        for l,lang in enumerate(LANGS):
            ix=p['lang']==l;v=c[ix].sum(0)
            per.append(dict(corpus=ds,checkpoint=seed,policy=name,language=lang,recordings=int(ix.sum()),S=int(v[0]),D=int(v[1]),I=int(v[2]),N=int(v[3]),WER=float(100*v[:3].sum()/v[3])))
    return rows,per
