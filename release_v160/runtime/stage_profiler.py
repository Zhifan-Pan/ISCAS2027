"""Separate instrumented execution; stage times never replace clean timing data."""
from collections import defaultdict
from contextlib import contextmanager, ExitStack
from unittest.mock import patch
import time


class StageProfiler:
    def __init__(self):
        self.stack=['host_sync_remainder']
        self.values=defaultdict(float)
        self.calls=defaultdict(int)
        self.start=None
        self.last=None

    def tick(self):
        import torch
        torch.cuda.synchronize()
        now=time.perf_counter()
        self.values[self.stack[-1]]+=(now-self.last)*1000
        self.last=now

    @contextmanager
    def phase(self,name):
        self.tick();self.stack.append(name);self.calls[name]+=1
        try:yield
        finally:self.tick();assert self.stack.pop()==name

    def begin(self):
        import torch
        torch.cuda.synchronize();self.start=self.last=time.perf_counter()

    def end(self):
        self.tick();assert self.stack==['host_sync_remainder']
        total=(self.last-self.start)*1000
        assert abs(sum(self.values.values())-total)<1e-6
        names=['preprocess_encoder','first_search','extra_fallback','teacher_score','PLL','routing','host_sync_remainder']
        return dict(end_to_end_ms=total,exclusive_ms={n:self.values[n] for n in names},
                    calls=dict(self.calls),partition_residual_ms=total-sum(self.values.values()),
                    instrumentation='Synchronized wall-clock intervals; nested child intervals removed from parent; synchronization overhead included')

    def wrapped(self,fn,label):
        def call(*args,**kwargs):
            with self.phase(label):return fn(*args,**kwargs)
        return call

    @contextmanager
    def instrument(self,runner):
        import soundfile
        import scipy.signal
        from transformers.generation.utils import GenerationMixin
        original_generate=GenerationMixin.generate
        def generate(model,*args,**kwargs):
            cfg=kwargs['generation_config']
            label='first_search' if not cfg.do_sample and cfg.num_beams==5 else 'extra_fallback'
            with self.phase(label):return original_generate(model,*args,**kwargs)
        extractor=type(runner.engine.proc.feature_extractor)
        with ExitStack() as stack:
            for obj,name,label in [(soundfile,'read','preprocess_encoder'),
                    (scipy.signal,'resample_poly','preprocess_encoder'),
                    (extractor,'__call__','preprocess_encoder'),
                    (runner.engine,'encode','preprocess_encoder'),
                    (runner.engine,'logps','teacher_score'),
                    (runner.pll,'score_text','PLL')]:
                stack.enter_context(patch.object(obj,name,self.wrapped(getattr(obj,name),label)))
            stack.enter_context(patch.object(GenerationMixin,'generate',generate))
            stack.enter_context(patch.object(runner,'profiler',self,create=True))
            yield
