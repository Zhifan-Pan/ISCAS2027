"""Exclusive actual audio paired timing; fixed samples and3sessions, no tuning."""
import os
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',TOKENIZERS_PARALLELISM='false')
from pathlib import Path
import sys,json,time,argparse,hashlib,gc
R=Path(__file__).resolve().parent.parent;A=R.parent;P=R.parents[2]
os.environ['ASR_REPRO_CONFIG']=str(A/'20261009_v79_stage_cost_energy/ASR_REPRO_CONFIG.json');sys.path.insert(0,str(P/'ASR_v2_CV27_run_20260919/submission_closeout_20260924/reproduction/portable'))
def save(p,d):
 t=p.with_name(p.name+'.tmp');t.write_text(json.dumps(d,indent=2)+'\n');t.replace(p)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--gpu',type=int,required=True);ap.add_argument('--slot',type=int,required=True);args=ap.parse_args();assert args.gpu in [0,1,2,3] and args.slot==0
 import torch,frozen_inference
 from runtime import SharedRuntime
 from activity_monitor import ActivityMonitor
 torch.set_num_threads(1);run=Path(os.environ['V156_WORKER_RUN']);monitor=ActivityMonitor(args.gpu,run/'ACTIVITY.json');deadline=time.monotonic()+12*3600;accepted=0
 import importlib.util
 spec=importlib.util.spec_from_file_location('v156_pair_queue',Path(__file__).parent/'pair_queue.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);claim=module.claim
 engine=frozen_inference.load_whisper_in_admitted_worker(101);pll=frozen_inference.load_pll_in_admitted_worker(batch=32);norm=frozen_inference.load_vendor('wer_rules_v3');beta=json.loads((R/'SELECTOR_LOCK.json').read_text())['101']['raw_beta'];runner=SharedRuntime(engine,pll,norm,beta);rows=json.loads((R/'private/TIMING_MANIFEST.json').read_text());expected=json.loads((R/'FROZEN_OUTPUT_HASHES.json').read_text())
 def wait_idle():
  while monitor.current():
   if time.monotonic()>deadline:raise RuntimeError('Bounded12h exclusive-window deadline exceeded')
   time.sleep(15)
 wait_idle();warm=[v for v in rows if not v['outer_trigger'] and not v['native_output_change']][:3]
 for row in warm:
  for policy in ['NplusR','SplusR']:runner.run(row['path'],row['lang'],row['uid'],row['split'],policy)
 while True:
  wait_idle();job=claim(R,rows)
  if job is None:break
  session,i,row,dst,claim_handle=job;out=dst.parent
  assert hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()==row['audio_sha256'];first=int(hashlib.sha256(f'V156_ORDER|{session}|{row["anon_id"]}'.encode()).hexdigest()[:8],16)%2;order=['NplusR','SplusR'] if first==0 else ['SplusR','NplusR'];attempt=0
  while True:
   wait_idle();attempt+=1;epoch=monitor.snapshot();pair=[]
   try:
    for policy in order:
     if monitor.current() or monitor.snapshot()!=epoch:raise InterruptedError('External activity before path')
     gc.collect();torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();start=time.perf_counter();result=runner.run(row['path'],row['lang'],row['uid'],row['split'],policy);torch.cuda.synchronize();elapsed=1000*(time.perf_counter()-start)
     if monitor.current() or monitor.snapshot()!=epoch:raise InterruptedError('External activity during pair')
     assert result['output_sha256']==expected[row['anon_id']][policy],('formal output mismatch',session,i,policy,row['anon_id']);pair.append({'policy':policy,'end_to_end_ms':elapsed,'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_reserved_bytes':torch.cuda.max_memory_reserved(),'work':result['work'],'native_events':result['native_events'],'bank_sizes':result['bank_sizes'],'selected_new':result['selected_new'],'output_sha256':result['output_sha256']})
    save(dst,{'session':session,'index':i,'id':row['anon_id'],'corpus':row['split'],'language':row['lang'],'stratum':row['stratum'],'inclusion_probability':row['inclusion_probability'],'population_count':row['population_count'],'sample_count':row['sample_count'],'outer_trigger':row['outer_trigger'],'native_output_change':row['native_output_change'],'path_order':order,'attempt':attempt,'physical_gpu':args.gpu,'paired':pair,'parity':True,'external_activity':False,'references_read':False,'worker_pid':os.getpid(),'worker_run':str(run),'execution_addendum':str(Path(__file__).parent/'PROTOCOL_ADDENDUM.json')})
    accepted+=1;save(run/'PROGRESS.json',{'round':session,'accepted_by_worker':accepted,'last_index':i,'last_id':row['anon_id'],'gpu':args.gpu});print('PAIRED',session,i+1,len(rows),flush=True)
    claim_handle.close()
    break
   except InterruptedError as exc:
    with (out/'EXCLUDED.jsonl').open('a') as log:log.write(json.dumps({'session':session,'index':i,'attempt':attempt,'reason':str(exc),'partial':pair})+'\n')
   if time.monotonic()>deadline:raise RuntimeError('Bounded12h ceiling')
 save(run/'COMPLETE.json',{'status':'COMPLETE_OR_ALL_REMAINING_CLAIMED','accepted_by_worker':accepted});monitor.close()
if __name__=='__main__':main()
