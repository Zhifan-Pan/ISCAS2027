"""Shared-first-pass fixed-policy inference; no site paths or reference labels.
Caller loads frozen engine/PLL after genuine site GPU admission. Both policies
reuse their own encoder states; Native+R preserves five first-pass beams and
S+R reuses its initial beam search in triggered native fallback. No cross-path
or cross-record neural cache is used. This implementation must pass parity.
"""
import copy,math,hashlib,zlib
from collections import Counter
import numpy as np
class SharedRuntime:
 def __init__(self,engine,pll,normalizer,beta):self.engine=engine;self.pll=pll;self.norm=normalizer;self.beta=np.asarray(beta,float)
 def run(self,path,language,uid,split,policy):
  import torch,soundfile as sf
  from scipy.signal import resample_poly
  from transformers.generation.utils import GenerationMixin
  from transformers.modeling_outputs import BaseModelOutput
  from transformers.generation.logits_process import WhisperNoSpeechDetection
  assert policy in ['NplusR','SplusR']
  e=self.engine;counts={'encoder_calls':0,'base_generation_calls':0,'reused_first_search':0,'PLL_calls':0,'PLL_tokens':0,'teacher_calls':0};native_events=[]
  encoder_hook=e.base.get_encoder().register_forward_hook(lambda *a:counts.__setitem__('encoder_calls',counts['encoder_calls']+1))
  original_generate=GenerationMixin.generate;original_need=e.base._need_fallback
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
   if context['mode']=='native' and first:cfg.num_return_sequences=5
   kwargs['generation_config']=cfg;counts['base_generation_calls']+=1
   out=original_generate(model,*args,**kwargs);out.past_key_values=None
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
    lp,mask=e.logps(w['feat'],w['mask'],language,c['token_ids'],w['enc']);counts['teacher_calls']+=1;body=np.asarray(lp,dtype=float)[np.asarray(mask,dtype=bool)];p=self.pll.score_text(c['text']);counts['PLL_calls']+=1;counts['PLL_tokens']+=int(p['ntokens']);words=self.norm.words(c['text'],language);grams=[tuple(words[j:j+4]) for j in range(max(0,len(words)-3))];freq=Counter(grams);rep=sum(freq[g]>=3 for g in grams)/max(1,len(grams));cache[k]=[float(body.mean()) if len(body) else 0.,float(p['pll']),math.log1p(len(body)),float(rep)]
   return cache[k]
  def select(w,native):
   bank=unique(w['beam']);base_size=len(bank)
   if native is not None:bank=unique(bank+[native])
   if len(bank)==1:return bank[0]['text'],False,base_size,len(bank)
   f=np.asarray([rawfeatures(c,w,{}) for c in bank]);f-=f[0];j=int((f@self.beta).argmax());return bank[j]['text'],j>=base_size,base_size,len(bank)
  try:
   GenerationMixin.generate=base_generate;e.base._need_fallback=need
   wave,sr=sf.read(path,dtype='float32')
   if wave.ndim>1:wave=wave.mean(axis=1)
   if sr!=16000:
    div=math.gcd(sr,16000);wave=resample_poly(wave,16000//div,sr//div).astype(np.float32)
   J=math.ceil(len(wave)/480000);rng=int(hashlib.sha256(f'V114|{split}|{language}|{uid}'.encode()).hexdigest()[:8],16);torch.manual_seed(rng);torch.cuda.manual_seed_all(rng)
   for j in range(J):
    part=wave[j*len(wave)//J:(j+1)*len(wave)//J];inp=e.proc.feature_extractor([part],sampling_rate=16000,return_tensors='pt',padding='max_length',max_length=480000,truncation=True,return_attention_mask=True);w={'feat':inp.input_features.to('cuda:0',dtype=torch.bfloat16),'mask':inp.attention_mask.to('cuda:0')};w['enc']=e.encode(w['feat']);states.append(w)
    if policy=='SplusR':
     context.update(state=w,window=j,mode='beam');e.generate(w['feat'],w['mask'],language,'N5',encoder=BaseModelOutput(last_hidden_state=w['enc'].last_hidden_state));raw=w['beam'][0]['text'].encode();w['trigger']=bool(raw and len(raw)/len(zlib.compress(raw))>2.4)
   outer=any(w.get('trigger',False) for w in states);selected=[];bank_sizes=[];first_beam_hashes=[]
   for j,w in enumerate(states):
    n=None
    if policy=='NplusR' or outer:
     context.update(state=w,window=j,mode='native')
     with torch.inference_mode():pred=e.model.generate(input_features=w['feat'],attention_mask=w['mask'],language=language,task='transcribe',max_new_tokens=444,num_beams=5,num_return_sequences=1,temperature=(0.,.2,.4,.6,.8,1.),compression_ratio_threshold=1.35,logprob_threshold=-1.,no_speech_threshold=.6,return_timestamps=False,condition_on_prev_tokens=False)
     n=e.record(pred[0].tolist(),0,'Native')
    text,took,kb,kf=select(w,n);outputs.append(text.strip());selected.append(took);bank_sizes.append([kb,kf]);first_beam_hashes.append([hashlib.sha256(c['text'].encode()).hexdigest() for c in unique(w['beam'])])
   result=' '.join(outputs).strip();return {'text':result,'output_sha256':hashlib.sha256(result.encode()).hexdigest(),'work':counts,'native_events':native_events,'selected_new':selected,'bank_sizes':bank_sizes,'first_beam_hashes':first_beam_hashes,'outer_trigger':outer if policy=='SplusR' else None,'window_count':J}
  finally:
   GenerationMixin.generate=original_generate;e.base._need_fallback=original_need;encoder_hook.remove()
