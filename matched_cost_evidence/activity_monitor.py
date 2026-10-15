"""Observe physical-card process activity without creating a CUDA context."""
import os,time,json,threading,datetime
from pathlib import Path
import pynvml

class ActivityMonitor:
    def __init__(self,gpu,output):
        pynvml.nvmlInit()
        self.handle=pynvml.nvmlDeviceGetHandleByIndex(gpu)
        self.pid=os.getpid();self.output=Path(output);self.lock=threading.Lock()
        self.epoch=0;self.events=[];self.last=();self.error=None;self.stop=threading.Event()
        self.thread=threading.Thread(target=self._loop,daemon=True);self.thread.start()

    def current(self):
        if self.error:raise RuntimeError('GPU activity monitor failed: '+self.error)
        pids=tuple(sorted(p.pid for p in pynvml.nvmlDeviceGetComputeRunningProcesses(self.handle) if p.pid!=self.pid))
        with self.lock:
            if pids:self.epoch+=1
            if pids!=self.last:
                self.events.append({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'monotonic':time.monotonic(),'external_pids':list(pids),'epoch':self.epoch})
                self.last=pids
                tmp=self.output.with_suffix('.tmp');tmp.write_text(json.dumps({'interval_seconds':.1,'events':self.events},indent=2)+'\n');tmp.replace(self.output)
        return list(pids)

    def snapshot(self):
        with self.lock:return self.epoch

    def _loop(self):
        try:
            while not self.stop.is_set():
                self.current();self.stop.wait(.1)
        except Exception as error:self.error=repr(error)

    def close(self):
        self.stop.set();self.thread.join();pynvml.nvmlShutdown()
