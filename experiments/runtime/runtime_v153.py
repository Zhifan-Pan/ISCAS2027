# V153 implementation candidate. GPU parity and timing NOT RUN.
# Call only from a separately admitted worker; historical RNG is unchanged.
# One recording-level seed; no window-local skipping or cross-path cache.
"""Shared-first-pass fixed-policy inference; no site paths or reference labels.
Caller loads frozen engine/PLL after genuine site GPU admission. Both policies
reuse their own encoder states; Native+R preserves five first-pass beams and
S+R reuses its initial beam search in triggered native fallback. No cross-path
or cross-record neural cache is used. This implementation must pass parity.
"""
import copy,math,hashlib,zlib,json
from collections import Counter
import numpy as np
from feature_scoring import score_raw
class SharedRuntime:
 def __init__(self,engine,pll,normalizer,beta,beta_h3):self.engine=engine;self.pll=pll;self.norm=normalizer;self.beta=np.asarray(beta,float);self.beta_h3=np.asarray(beta_h3,float);assert self.beta.shape==(4,) and self.beta_h3.shape==(3,)
 def run(self,path,language,uid,split,policy):
  import torch,soundfile as sf
  from scipy.signal import resample_poly
  from transformers.generation.utils import GenerationMixin
  from transformers.modeling_outputs import BaseModelOutput
  from transformers.generation.logits_process import WhisperNoSpeechDetection
  assert policy in ['Native','RawTop1','B','NplusR','SplusR','SDirect','H3Direct']
  collect=bool(getattr(self,'collect_bundle',False));assert not collect or policy=='NplusR'
  audit=bool(getattr(self,'audit_trace',False));traces=[];rng_calls=[]
  def rng_digest():return {'cpu':hashlib.sha256(torch.get_rng_state().numpy().tobytes()).hexdigest(),'cuda':hashlib.sha256(torch.cuda.get_rng_state().cpu().numpy().tobytes()).hexdigest()}
  def candidate_digest(c):return {'text_sha256':hashlib.sha256(c['text'].encode()).hexdigest(),'token_sha256':hashlib.sha256(json.dumps([int(x) for x in c['token_ids']],separators=(',',':')).encode()).hexdigest()}
  e=self.engine;counts={'encoder_calls':0,'base_generation_calls':0,'reused_first_search':0,'PLL_calls':0,'PLL_tokens':0,'PLL_forwards':0,'PLL_head_forwards':0,'teacher_calls':0};native_events=[]
  encoder_hook=None
  original_generate=GenerationMixin.generate;original_need=e.base._need_fallback
  pll_hook=None;head_hook=None
  if policy not in ['RawTop1','H3Direct','Native']:
   if self.pll is None:raise RuntimeError('G4 paths require a PLL scorer')
  context={};states=[];outputs=[]
  def need(*args,**kwargs):
   result=original_need(*args,**kwargs);params=dict(zip(['seek_sequence','seek_outputs','index','logits_processor','generation_config','vocab_size','temperature'],args));params.update(kwargs);gc=params['generation_config'];procs=params['logits_processor'];prob=None
   for p in procs:
    if isinstance(p,WhisperNoSpeechDetection) and p._no_speech_prob is not None:prob=float(p._no_speech_prob[0].detach().cpu())
   native_events.append({'window':context['window'],'temperature':params['temperature'],'needs_fallback':bool(result[0]),'should_skip':bool(result[1]),'tokens_with_EOS':int(params['seek_sequence'].numel()),'no_speech_probability':prob})
   return result
  def top1(out):
   values=dict(out);values.pop('past_key_values',None)
   for k in ['sequences','sequences_scores','beam_indices']:
    if k in values:values[k]=values[k][:1]
   return type(out)(**values)
  def base_generate(model,*args,**kwargs):
   if model is not e.base:return original_generate(model,*args,**kwargs)
   w=context['state'];gc=kwargs['generation_config'];prefix=kwargs['decoder_input_ids'];procs=kwargs.get('logits_processor',[])
   kwargs['encoder_outputs']=BaseModelOutput(last_hidden_state=w['enc'].last_hidden_state)
   for p in procs:
    if isinstance(p,WhisperNoSpeechDetection):p.inputs['encoder_outputs']=BaseModelOutput(last_hidden_state=w['enc'].last_hidden_state)
   first=not gc.do_sample and gc.num_beams==5
   if context['mode']=='native' and first and w.get('first') is not None:
    assert torch.equal(prefix,w['prefix']), 'Initial/native decoder prefixes differ; cannot share'
    for p in procs:
     if isinstance(p,WhisperNoSpeechDetection):p(prefix,w['first'].scores[0])
    counts['reused_first_search']+=1;return top1(w['first'])
   cfg=copy.deepcopy(gc);cfg.return_dict_in_generate=True;cfg.output_scores=True
   if context['mode']=='native' and first:cfg.num_return_sequences=1 if policy=='Native' else 5
   kwargs['generation_config']=cfg;counts['base_generation_calls']+=1
   before=rng_digest() if audit else None
   out=original_generate(model,*args,**kwargs);out.past_key_values=None
   if audit:rng_calls.append({'window':context['window'],'mode':context['mode'],'do_sample':bool(gc.do_sample),'num_beams':int(gc.num_beams),'before':before,'after':rng_digest()})
   if first:
    w['first']=out;w['prefix']=prefix.detach().clone();start=prefix.shape[-1]
    w['beam']=[e.record(v[start:].tolist(),j,'B5') for j,v in enumerate(out.sequences)]
   if context['mode']=='beam':return out.sequences
   return top1(out) if first else out
  def unique(candidates):
   seen=set();items=[]
   for c in candidates:
    key=tuple(self.norm.words(c['text'],language))
    if key not in seen:seen.add(key);items.append(c)
   return items
  def rawfeatures(c,w,cache):
   k=(c['text'],tuple(c['token_ids']))
   if k not in cache:
    cache[k]=score_raw(e,self.norm,c,w,language,counts,'H3' if policy=='H3Direct' else 'G4',None if policy=='H3Direct' else self.pll)
   return cache[k]
  def _select(w,native):
   bank=unique(w['beam']);base_size=len(bank)
   if native is not None:bank=unique(bank+[native])
   if len(bank)==1:
    if collect:w['bundle']={'B':bank[0]['text'],'Native':native['text'],'NplusR':bank[0]['text']}
    return bank[0]['text'],False,base_size,len(bank)
   f=np.asarray([rawfeatures(c,w,{}) for c in bank]);f-=f[0];scores=f@(self.beta_h3 if policy=='H3Direct' else self.beta);j=int(scores.argmax())
   if collect:w['bundle']={'B':bank[int(scores[:base_size].argmax())]['text'],'Native':native['text'],'NplusR':bank[j]['text']}
   return bank[j]['text'],j>=base_size,base_size,len(bank)
  def select(w,native):
   profiler=getattr(self,'profiler',None)
   if profiler is None:return _select(w,native)
   with profiler.phase('routing'):return _select(w,native)
  try:
   encoder_hook=e.base.get_encoder().register_forward_hook(lambda *a:counts.__setitem__('encoder_calls',counts['encoder_calls']+1))
   if self.pll is not None:
    pll_hook=self.pll.model.roberta.register_forward_hook(lambda *a:counts.__setitem__('PLL_forwards',counts['PLL_forwards']+1))
    head_hook=self.pll.model.lm_head.register_forward_hook(lambda *a:counts.__setitem__('PLL_head_forwards',counts['PLL_head_forwards']+1))
   GenerationMixin.generate=base_generate;e.base._need_fallback=need
   wave,sr=sf.read(path,dtype='float32')
   if wave.ndim>1:wave=wave.mean(axis=1)
   if sr!=16000:
    div=math.gcd(sr,16000);wave=resample_poly(wave,16000//div,sr//div).astype(np.float32)
   J=math.ceil(len(wave)/480000);rng=int(hashlib.sha256(f'V114|{split}|{language}|{uid}'.encode()).hexdigest()[:8],16);torch.manual_seed(rng);torch.cuda.manual_seed_all(rng)
   initial_rng=rng_digest() if audit else None
   for j in range(J):
    part=wave[j*len(wave)//J:(j+1)*len(wave)//J];inp=e.proc.feature_extractor([part],sampling_rate=16000,return_tensors='pt',padding='max_length',max_length=480000,truncation=True,return_attention_mask=True);w={'feat':inp.input_features.to('cuda:0',dtype=torch.bfloat16),'mask':inp.attention_mask.to('cuda:0')};w['enc']=e.encode(w['feat']);states.append(w)
    if policy in ['SplusR','B','SDirect','RawTop1','H3Direct']:
     context.update(state=w,window=j,mode='beam');e.generate(w['feat'],w['mask'],language,'N5',encoder=BaseModelOutput(last_hidden_state=w['enc'].last_hidden_state));raw=w['beam'][0]['text'].encode();w['trigger']=bool(raw and len(raw)/len(zlib.compress(raw))>2.4)
   outer=any(w.get('trigger',False) for w in states);selected=[];bank_sizes=[];first_beam_hashes=[]
   for j,w in enumerate(states):
    n=None
    if policy in ['NplusR','Native'] or (policy in ['SplusR','SDirect','H3Direct'] and outer):
     context.update(state=w,window=j,mode='native')
     with torch.inference_mode():pred=e.model.generate(input_features=w['feat'],attention_mask=w['mask'],language=language,task='transcribe',max_new_tokens=444,num_beams=5,num_return_sequences=1,temperature=(0.,.2,.4,.6,.8,1.),compression_ratio_threshold=1.35,logprob_threshold=-1.,no_speech_threshold=.6,return_timestamps=False,condition_on_prev_tokens=False)
     n=e.record(pred[0].tolist(),0,'Native')
    if policy=='Native' or (policy in ['SDirect','H3Direct'] and outer):text,took,kb,kf=n['text'],True,1,1
    elif policy=='RawTop1':text,took,kb,kf=w['beam'][0]['text'],False,len(unique(w['beam'])),len(unique(w['beam']))
    else:text,took,kb,kf=select(w,n)
    outputs.append(text.strip());selected.append(took);bank_sizes.append([kb,kf]);first_beam_hashes.append([hashlib.sha256(c['text'].encode()).hexdigest() for c in unique(w['beam'])])
    if audit:traces.append({'window':j,'beam':[candidate_digest(c) for c in unique(w['beam'])],'native':None if n is None else candidate_digest(n),'output_sha256':hashlib.sha256(text.encode()).hexdigest()})
   result=' '.join(outputs).strip();bundle={}
   if collect:
    for key in ('B','Native','NplusR'):bundle[key]=' '.join(w['bundle'][key].strip() for w in states).strip()
    flags=[]
    for w in states:
     raw=w['beam'][0]['text'].encode();flags.append(bool(raw and len(raw)/len(zlib.compress(raw))>2.4))
    bundle['outer_trigger']=any(flags);bundle['SplusR']=bundle['NplusR'] if any(flags) else bundle['B']
   if policy in ['RawTop1','H3Direct','Native']:
    assert counts['PLL_calls']==counts['PLL_tokens']==counts['PLL_forwards']==counts['PLL_head_forwards']==0
   return {'bundle':bundle,'text':result,'output_sha256':hashlib.sha256(result.encode()).hexdigest(),'work':counts,'native_events':native_events,'selected_new':selected,'bank_sizes':bank_sizes,'first_beam_hashes':first_beam_hashes,'outer_trigger':outer if policy in ['SplusR','SDirect','H3Direct'] else None,'window_count':J,'trace':traces,'rng_trace':{'seed':rng,'initial':initial_rng,'final':rng_digest() if audit else None,'generation_calls':rng_calls}}
  finally:
   GenerationMixin.generate=original_generate;e.base._need_fallback=original_need
   if encoder_hook is not None:encoder_hook.remove()
   if pll_hook is not None:pll_hook.remove()
   if head_hook is not None:head_hook.remove()
