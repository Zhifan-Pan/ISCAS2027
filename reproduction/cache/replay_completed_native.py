"""Portable final native/comparator means and paired conditional intervals."""
from pathlib import Path
import json,numpy as np
R=Path(__file__).resolve().parent;D=R/'data'
def arrays(name):
 with np.load(D/name,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def macro(c,l):return float(np.mean([100*c[l==j,:3].sum()/c[l==j,3].sum() for j in range(5)]))
def close(x,y):assert abs(x-y)<1e-9,(x,y)
old=arrays('NATIVE_COUNTS.npz');new=arrays('NATIVE_REPLICATION202303.npz');expected=json.loads((D/'ALL_CHECKPOINT_COMPARISONS.json').read_text());oldmap={str(a):i for i,a in enumerate(old['ids'])};newmap={(int(s),str(a)):i for i,(s,a) in enumerate(zip(new['seeds'],new['ids']))};result={'status':'PASS','scope':'Portable cached means/paired CV27 interval; not raw inference','datasets':{}}
for ds in ['FLEURS','CV27']:
 means=[];diff=[];nearest=[]
 for seed in [101,202,303]:
  z=arrays(f'COUNTS_{ds}_{seed}.npz');nat=old['counts'][[oldmap[str(a)] for a in z['ids']]] if seed==101 else new['counts'][[newmap[(seed,str(a))] for a in z['ids']]];np.testing.assert_array_equal(nat[:,3],z['NoAcquisition'][:,3]);m=macro(nat,z['lang']);point=next(v for v in expected['datasets'][ds]['per_checkpoint'] if v['seed']==seed);close(m,point['macro_WER']['Native']);means.append(m);diff.append(nat[:,:3].sum(1)-z['HFFallbackFixed'][:,:3].sum(1));c=arrays(f'NATIVE_RESCORE_COUNTS_{ds}_{seed}.npz');np.testing.assert_array_equal(c['ids'],z['ids']);nearest.append(macro(c['counts'],c['lang']))
 result['datasets'][ds]={'native_macro_WER_per_checkpoint':means,'native_macro_WER_mean':float(np.mean(means)),'fixed_native_rescore_macro_WER_mean':float(np.mean(nearest))};close(np.mean(means),expected['datasets'][ds]['macro_WER_3checkpoint_mean']['Native'])
 if ds=='CV27':
  meta=arrays('CV27_COMPONENTS.npz');np.testing.assert_array_equal(meta['ids'],z['ids']);ed=-np.mean(diff,axis=0);suff=[]
  for j in range(5):
   ix=z['lang']==j;_,g=np.unique(meta['components'][ix],return_inverse=True);suff.append((np.bincount(g,weights=ed[ix]),np.bincount(g,weights=nat[ix,3])))
  rng=np.random.default_rng(15301);draw=[]
  for _ in range(2000):
   v=0.
   for e,n in suff:
    take=rng.choice(len(n),len(n),replace=True);v+=20*e[take].sum()/n[take].sum()
   draw.append(v)
  bounds=np.quantile(draw,[.025,.975]);index=expected['datasets'][ds]['SCA_minus_Native_order'].index('HFFallbackFixed');target=expected['datasets'][ds]['CI95_SCA_minus_Native_pp'];np.testing.assert_allclose(bounds,[target[0][index],target[1][index]],atol=1e-10,rtol=0);result['datasets'][ds]['CI95_HF_minus_native_pp']=bounds.tolist()
(R/'COMPLETED_NATIVE_REPLAY.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
