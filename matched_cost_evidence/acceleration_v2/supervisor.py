"""Four-card opportunistic exclusive scheduling for existing fixed paired rounds."""
from pathlib import Path
import datetime,fcntl,json,os,subprocess,time,signal,hashlib
import pynvml
S=Path(__file__).resolve().parent;R=S.parent
W=Path('/home/mhmt_stu/Code/ISCAS2027_working_v63');PY='/home/mhmt_stu/Code/.venv/bin/python'
UUID={0:'GPU-4101e1a5-0311-a5ec-672e-537e8d76bbc9',1:'GPU-0cd1f798-651c-fc4e-959b-e6d0e8bd6bd7',2:'GPU-42d64a96-e099-5fb3-124f-03c25059e7c1',3:'GPU-c9dacf12-0b95-828c-37fc-b84e69a828ea'}
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,v):
 t=p.with_name(p.name+'.tmp');t.write_text(json.dumps(v,indent=2)+'\n');t.replace(p)
def identity(pid):
 try:
  x=(Path(f'/proc/{pid}')/'stat').read_text().rsplit(')',1)[1].split()
  if x[0]=='Z':return None
  return dict(pid=pid,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),starttime_ticks=int(x[19]))
 except FileNotFoundError:return None
def counts():
 return {i:len([p for p in (R/'timing'/f'session{i}').glob('*.json') if len(p.stem)==64]) for i in range(3)}
def card(gpu):
 h=pynvml.nvmlDeviceGetHandleByIndex(gpu);u=pynvml.nvmlDeviceGetUUID(h)
 if isinstance(u,bytes):u=u.decode()
 assert u==UUID[gpu]
 return [p.pid for p in pynvml.nvmlDeviceGetComputeRunningProcesses(h)],pynvml.nvmlDeviceGetMemoryInfo(h).free
def publish(jobs,status='RUNNING',extra=None):
 state=dict(status=status,active_jobs=[{k:v for k,v in j.items() if k not in ['child','blocked_since']} for j in jobs.values()],accepted_pairs=counts(),rounds_total=3,pairs_per_round=727,scheduler='FOUR_CARD_ATOMIC_EXCLUSIVE',protocol_addendum=str(S/'PROTOCOL_ADDENDUM.json'),updated_utc=utc())
 if extra:state.update(extra)
 save(S/'SCHEDULING_STATE.json',state);save(R/'FORMAL_STATE.json',state)
 for p in [R/'RECOVERY_CAPSULE.json',W/'RECOVERY_CAPSULE.json',W/'RECOVERY_V116.json']:
  v=json.loads(p.read_text());v.update(updated_utc=utc(),active_jobs=state['active_jobs'],status='V116_DRAFT_FOUR_CARD_MATCHED_COST',protocol_addendum=str(S/'PROTOCOL_ADDENDUM.json'),four_card_preparation={'status':status,'preserved_and_current_pairs':state['accepted_pairs']},next_action='Four-card detached OS supervisor completes remaining fixed pairs; integrate verified cost summary once, no duplicate launches.');save(p,v)
 print(json.dumps(dict(event=status,pairs=state['accepted_pairs'],active=[(g,j['pid']) for g,j in jobs.items()])),flush=True)
def main():
 lock=(S/'scheduler.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for p in [R/'EXECUTION_LOCK.json',S/'ACCELERATION_EXECUTION_LOCK.json']:
  base=R if p.parent==R else S
  for n,h in json.loads(p.read_text()).items():assert hashlib.sha256((base/n).read_bytes()).hexdigest()==h,n
 pynvml.nvmlInit();jobs={};started=time.monotonic();last=None
 save(R/'FORMAL_SUPERVISOR.json',dict(pid=os.getpid(),identity=identity(os.getpid()),script=str(Path(__file__).resolve()),started_utc=utc()))
 try:
  while True:
   changed=False
   for gpu,j in list(jobs.items()):
    if identity(j['pid'])!=j['identity']:
     code=j['child'].wait();del jobs[gpu];changed=True
     if code not in [0,143,-15]:raise RuntimeError(f"Worker exit {code}: {j['log']}; no silent retries")
     continue
    pids,_=card(gpu);foreign=[p for p in pids if p!=j['pid']]
    if foreign:
     j.setdefault('blocked_since',time.monotonic())
     if time.monotonic()-j['blocked_since']>180 and not j.get('retiring'):
      # Stop only the registered identity of our waiting worker; never foreign jobs.
      assert identity(j['pid'])==j['identity'];os.kill(j['pid'],signal.SIGTERM);j['retiring']=True;changed=True
    else:j.pop('blocked_since',None)
   c=counts()
   if all(n==727 for n in c.values()) and not jobs:break
   if time.monotonic()-started>36*3600:raise RuntimeError('36h supervision ceiling')
   if not all(n==727 for n in c.values()):
    for gpu in range(4):
     if gpu in jobs:continue
     pids,free=card(gpu)
     if pids or free<8192*2**20:continue
     d=R/'runs'/'four_card'/f"gpu{gpu}_{time.time_ns()}";d.mkdir(parents=True)
     env=dict(os.environ,CUDA_VISIBLE_DEVICES=UUID[gpu],V156_WORKER_RUN=str(d))
     with (d/'worker.log').open('a') as log:child=subprocess.Popen([PY,str(R/'scripts/runner.py'),'--gpu',str(gpu),'--slot','0'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
     jobs[gpu]=dict(pid=child.pid,gpu=gpu,slot=0,identity=identity(child.pid),log=str(d/'worker.log'),child=child);changed=True
   marker=(tuple(c.items()),tuple((g,j['pid'],j.get('retiring',False)) for g,j in jobs.items()))
   if changed or marker!=last:publish(jobs);last=marker
   time.sleep(15)
  rows=json.loads((R/'private/TIMING_MANIFEST.json').read_text());hashes=json.loads((R/'FROZEN_OUTPUT_HASHES.json').read_text())
  for session in range(3):
   for row in rows:
    v=json.loads((R/'timing'/f'session{session}'/(row['anon_id']+'.json')).read_text());assert v['parity'] and not v['external_activity'];assert v['id']==row['anon_id'];assert {q['policy']:q['output_sha256'] for q in v['paired']}=={k:hashes[row['anon_id']][k] for k in ['NplusR','SplusR']}
   save(R/'timing'/f'session{session}'/'COMPLETE.json',dict(status='COMPLETE',session=session,paired_records=727,all_output_hashes_match=True,exclusive_observation=True,execution_addendum=str(S/'PROTOCOL_ADDENDUM.json')))
  publish(jobs,'ANALYZING')
  with (R/'timing_analysis_v2.log').open('a') as log:p=subprocess.run([PY,str(S/'summarize_timing.py')],env=dict(os.environ,CUDA_VISIBLE_DEVICES=''),stdout=log,stderr=subprocess.STDOUT)
  assert p.returncode==0,'Analyzer failed: timing_analysis_v2.log'
  publish(jobs,'COMPLETE_VERIFIED',{'summary':str(R/'timing_summary.json')})
 except Exception as e:publish(jobs,'ACTION_REQUIRED',{'error':repr(e)});raise
 finally:pynvml.nvmlShutdown()
if __name__=='__main__':main()
