"""Site-independent numerical replay; cached evidence only, no model or GPU."""
from pathlib import Path
import hashlib,json,numpy as np
ROOT=Path(__file__).resolve().parent;D=ROOT/'data'
def load(name):return json.loads((D/name).read_text())
def arrays(name):
 with np.load(D/name,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def macro(c,l):return float(np.mean([100*c[l==j,:3].sum()/c[l==j,3].sum() for j in range(5)]))
def close(a,b):assert abs(a-b)<1e-9,(a,b)
for name,expected in json.loads((ROOT/'INPUT_SHA256.json').read_text()).items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,name
sources=load('RESULTS.json');summary=load('GATE_SUMMARY.json');choice=load('SOURCE_ACCEPTANCE_OOF_DEV_LOCK.json')['decision'];report={'status':'PASS','scope':'CPU cached numerical replay; not original training/inference','sources':{},'native101':{},'oracle_net_ratio':{},'component_deletion':{},'checked_gate_points':0}
for ds in ['FLEURS','CV27']:
 means={}
 for seed in [101,202,303]:
  z=arrays(f'COUNTS_{ds}_{seed}.npz')
  for name in ['NoAcquisition','GreedyDirect','GreedyFixed','GreedyRefit','Temp02Direct','Temp02Fixed','Temp02Refit','HFFallbackDirect','HFFallbackFixed','HFFallbackRefit']:means.setdefault(name,[]).append(macro(z[name],z['lang']))
  g=arrays(f'GATES_{ds}_{seed}.npz');lock=load(f'FINAL_DEV_LOCK_{seed}.json');single=~np.isin(g['ids'],load('LONG_FLEURS_IDS.json')) if ds=='FLEURS' else np.ones(len(g['ids']),bool)
  for variant in ['original9','signal12']:
   model=lock['variants'][variant]['learner'];x=g['z9'] if variant=='original9' else np.column_stack([g['z9'],g['raw']]);score=-(np.column_stack([np.ones(len(x)),(x-model['mean'])/model['scale']])@np.asarray(model['coef']))
   for q in [.001,.003,.01,.03,.1,.25,.5,.75,1.]:
    key=variant+'_'+str(q);tau=lock['variants'][variant]['thresholds'][str(q)];flags=g[key];expected=g['eligible']&(score<tau if q<1 else True);np.testing.assert_array_equal(flags[single],expected[single]);counts=np.where(flags[:,None],g['full'],g['base']);means.setdefault(key,[]).append(macro(counts,g['lang']));report['checked_gate_points']+=1
 report['sources'][ds]={}
 for name,values in means.items():
  value=float(np.mean(values))
  if name.startswith(('original9','signal12')):close(value,summary[ds][name]['macro_WER'])
  else:close(value,sources['datasets'][ds]['macro_WER'][name]);report['sources'][ds][name]=value
for src in ['Greedy','Temp02','HFFallback']:
 values={'Direct':[],'Reselect':[]}
 for seed in [101,202,303]:
  z=arrays(f'OOF_DEV_SOURCE_{seed}_{src}.npz');values['Direct'].append(macro(z['direct'],z['lang']));values['Reselect'].append(macro(z['reselect'],z['lang']))
 m={k:float(np.mean(v)) for k,v in values.items()}
 for k,v in m.items():close(v,choice[src]['DEV_macro_WER'][k])
 assert choice[src]['acceptance']==('Direct' if m['Direct']<m['Reselect'] else 'Reselect')
native=arrays('NATIVE_COUNTS.npz')
for ds,label in [('TEST','FLEURS'),('CV27','CV27')]:
 ix=native['corpus']==ds;report['native101'][label]=macro(native['counts'][ix],native['lang'][ix])
meta=arrays('CV27_COMPONENTS.npz');diags=load('CACHE_DIAGNOSTICS.json');net=[]
for seed in [101,202,303]:
 o=arrays(f'ORACLE_CV27_{seed}.npz');z=arrays(f'COUNTS_CV27_{seed}.npz');np.testing.assert_array_equal(o['ids'],meta['ids']);flags=o['flags'];net.append(float(100*(o['weights']*flags*(o['beam_ED']-o['full_ED'])).sum()/(o['weights']*flags*o['oracle_delta']).sum()))
 b=z['NoAcquisition'];c=z['GreedyFixed'];gain=b[:,:3].sum(1)-c[:,:3].sum(1);point=macro(b,meta['lang'])-macro(c,meta['lang']);deltas=[]
 for l in range(5):
  ix=meta['lang']==l;_,inv=np.unique(meta['components'][ix],return_inverse=True);eg=np.bincount(inv,weights=gain[ix]);ng=np.bincount(inv,weights=b[ix,3]);E=eg.sum();N=ng.sum();ok=ng<N;deltas.extend((20*(E-eg[ok])/(N-ng[ok])-20*E/N).tolist())
 bounds=[point+min(deltas),point+max(deltas)];expected=next(v for v in diags['sparsity'] if v['seed']==seed)['LOCO_gain_range_pp'];np.testing.assert_allclose(bounds,expected,atol=1e-10,rtol=0);report['component_deletion'][str(seed)]=bounds
report['oracle_net_ratio']={'per_checkpoint_pct':net,'mean_pct':float(np.mean(net))};close(float(np.mean(net)),diags['oracle_net_mean_pct'])
nearest=load('NATIVE_RESCORE_RESULTS.json')
for ds in ['FLEURS','CV27']:
    c=arrays(f'NATIVE_RESCORE_COUNTS_{ds}_101.npz');z=arrays(f'COUNTS_{ds}_101.npz');np.testing.assert_array_equal(c['ids'],z['ids']);np.testing.assert_array_equal(c['counts'][:,3],z['NoAcquisition'][:,3]);close(macro(c['counts'],c['lang']),nearest['datasets'][ds]['macro_WER']['NativeRescore'])
report['nearest_fixed_coefficient_control']=nearest['datasets']
report['HF_OOF_nonzero_instances']=load('OOF_DECISION_INFORMATION.json')
(ROOT/'REPLAY_REPORT.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'PASS','gate_points':report['checked_gate_points'],'native101':report['native101'],'oracle_net_mean_pct':np.mean(net),'absolute_site_imports':False}))
