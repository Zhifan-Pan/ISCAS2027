"""Fixed-design paired mean estimates; sampling CI conditional on3sessions."""
from pathlib import Path
import os,json,hashlib,numpy as np
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
R=Path(__file__).resolve().parent.parent
rows=json.loads((R/'private/TIMING_MANIFEST.json').read_text());strata=json.loads((R/'TIMING_STRATA.json').read_text());expected=json.loads((R/'FROZEN_OUTPUT_HASHES.json').read_text());times=np.zeros((len(rows),3,2));peaks=np.zeros_like(times);raw=[];session_gpu={};allocation={}
for session in range(3):
 assert json.loads((R/'timing'/f'session{session}'/'COMPLETE.json').read_text())['status']=='COMPLETE'
 for i,row in enumerate(rows):
  v=json.loads((R/'timing'/f'session{session}'/(row['anon_id']+'.json')).read_text());assert v['id']==row['anon_id'] and v['parity'] and not v['external_activity'];gpu=int(v['physical_gpu']);assert gpu in [0,1,2,3];session_gpu.setdefault(session,set()).add(gpu);allocation[(i,session)]=gpu;pair={x['policy']:x for x in v['paired']};assert set(pair)=={'NplusR','SplusR'}
  for j,p in enumerate(['NplusR','SplusR']):
   q=pair[p];assert q['output_sha256']==expected[row['anon_id']][p];assert q['end_to_end_ms']>0;times[i,session,j]=q['end_to_end_ms'];peaks[i,session,j]=q['peak_allocated_bytes']/2**20;raw.append(dict(session=session,id=v['id'],corpus=v['corpus'],language=v['language'],stratum=v['stratum'],policy=p,ms=q['end_to_end_ms'],MiB=peaks[i,session,j],inclusion_probability=v['inclusion_probability'],work=q['work'],native_events=q['native_events']))
with (R/'timing_raw.jsonl').open('w') as out:
 for v in raw:out.write(json.dumps(v)+'\n')
result={'status':'PASS','scope':'Exclusive per-card A40 on authorized idle cards, checkpoint101, complete audio; three measurement rounds with same-card path pairs. Dynamic device allocation frozen before execution.','sessions':3,'policies':['NplusR','SplusR'],'uncertainty_scope':'Paired stratified record-bootstrap conditional on3observed measurement rounds and actual device allocation; census strata fixed; ordinary finite-population correction. Session variation reported separately, not a reliable population hardware CI from3rounds.','datasets':{}}
for ds in ['TEST','CV27']:
 st=[s for s in strata if s['corpus']==ds];N=sum(s['population_count'] for s in st);mean=np.zeros((3,2));groups=[];selected=np.array([r['split']==ds for r in rows])
 for s in st:
  ix=np.array([r['stratum']==s['stratum'] for r in rows]);v=times[ix];assert len(v)==s['sample_count'];contribution=s['population_count']*v.mean(0)/N;mean+=contribution;groups.append((s,v,contribution))
 mu=mean.mean(0);delta=mu[0]-mu[1];saving=1-mu[1]/mu[0];rng=np.random.default_rng(15601);draw=[]
 for _ in range(4000):
  m=np.zeros((3,2))
  for s,v,c in groups:
   n=len(v);M=s['population_count']
   if n==M:m+=c;continue
   take=rng.choice(n,n,replace=True);boot=v[take].mean(0);fpc=np.sqrt((M-n)/(M-1));m+=c+(M/N)*fpc*(boot-v.mean(0))
  mm=m.mean(0);draw.append([mm[0],mm[1],mm[0]-mm[1],1-mm[1]/mm[0]])
 bounds=np.quantile(draw,[.025,.975],axis=0);per=[]
 for session in range(3):per.append({'session':session,'physical_gpus':sorted(session_gpu[session]),'NplusR_mean_ms':float(mean[session,0]),'SplusR_mean_ms':float(mean[session,1]),'difference_ms':float(mean[session,0]-mean[session,1]),'relative_saving_pct':float(100*(1-mean[session,1]/mean[session,0]))})
 result['datasets'][ds]={'population_records':N,'sample_records':int(selected.sum()),'session_estimates':per,'estimated_mean_ms':{'NplusR':float(mu[0]),'SplusR':float(mu[1])},'NplusR_minus_SplusR_ms':float(delta),'SplusR_relative_saving_pct':float(100*saving),'CI95_mean_N_R_S_R_difference_ms_and_saving_fraction':bounds.tolist(),'observed_session_difference_range_ms':[float((mean[:,0]-mean[:,1]).min()),float((mean[:,0]-mean[:,1]).max())],'peak_allocated_MiB':{'NplusR':float(peaks[selected,:,0].max()),'SplusR':float(peaks[selected,:,1].max())},'census_records':sum(s['sample_count'] for s in st if s['region']=='behavior_census'),'ordinary_sample_records':sum(s['sample_count'] for s in st if s['region']=='ordinary_sample')}
result['protocol_addendum']=str(R/'acceleration_v2/PROTOCOL_ADDENDUM.json');result['protocol_addendum_sha256']=hashlib.sha256((R/'acceleration_v2/PROTOCOL_ADDENDUM.json').read_bytes()).hexdigest();result['round_physical_gpus']={str(k):sorted(v) for k,v in session_gpu.items()}
for ds,v in result['datasets'].items():
 v['device_allocation_descriptive']={}
 for gpu in sorted({g for gs in session_gpu.values() for g in gs}):
  vals=[times[i,s,:] for (i,s),g in allocation.items() if g==gpu and rows[i]['split']==ds]
  if not vals:continue
  z=np.asarray(vals);v['device_allocation_descriptive'][str(gpu)]={'accepted_pairs':len(z),'unweighted_sample_mean_ms':z.mean(0).tolist(),'scope':'Selected allocation subset, not a population hardware comparison'}
(R/'timing_summary.json').write_text(json.dumps(result,indent=2)+'\n');(R/'timing_parity.json').write_text(json.dumps({'status':'PASS','paired_records':len(rows),'sessions':3,'path_calls':len(rows)*3*2,'all_immutable_output_hashes_match':True,'all_included_pairs_exclusive':True},indent=2)+'\n');print(json.dumps(result,indent=2))
