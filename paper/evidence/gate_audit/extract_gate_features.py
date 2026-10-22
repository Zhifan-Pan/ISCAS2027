"""Export numeric top-beam gate evidence from immutable private caches, CPU only.

No audio access, model calls, fitting, or transcript/token publication.
The public output preserves ordering and per-window numeric ratios only.
"""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
import argparse, ast, hashlib, importlib.util, json, math, zlib
from collections import Counter
from pathlib import Path
import numpy as np

LANGS=['ar','fa','pl','tr','it']; SEEDS=[101,202,303]
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()
def arrays(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True,type=Path);ap.add_argument('--author-root',required=True,type=Path);ap.add_argument('--output',required=True,type=Path);a=ap.parse_args()
    r,root,out=a.repo.resolve(),a.author_root.resolve(),a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    manifest={}; checks=[]
    def track(p):
        p=Path(p);manifest[str(p)]={'sha256':sha(p),'bytes':p.stat().st_size};return p
    idx=json.loads(track(root/'ASR_v2_CV27_run_20260919/review_strengthening_20260923/reproduction/config/CACHE_INDEX.json').read_text())
    freeze=json.loads(track(r/'reproduction/portable/bindings/evidence/GENERATION_FREEZE.json').read_text())
    cfgpath=track(freeze['model_config']['path']);assert sha(cfgpath)==freeze['model_config']['sha256'];cfg=json.loads(cfgpath.read_text())
    eos=cfg['eos_token_id'];width=int(math.log2(cfg['vocab_size'])/8)+1
    hfpath=next(Path(p) for p in freeze['native_sources'] if p.endswith('generation_whisper.py'))
    track(hfpath);assert sha(hfpath)==freeze['native_sources'][str(hfpath)]
    tree=ast.parse(hfpath.read_text());fn=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='_retrieve_compression_ratio')
    fn.decorator_list=[];module=ast.Module(body=[fn],type_ignores=[]);ast.fix_missing_locations(module);env={'math':math,'zlib':zlib};exec(compile(module,str(hfpath),'exec'),env);hf_ratio=env[fn.name]
    wpath=track(r/'reproduction/portable/vendor/wer_rules_v3.py');spec=importlib.util.spec_from_file_location('gate_wer',wpath);wer=importlib.util.module_from_spec(spec);spec.loader.exec_module(wer)
    ready_path=track(root/'artifacts/asr_official_fullaudio/20260929_v1/results/FULL_AUDIO_BANKS_READY.json');ready=json.loads(ready_path.read_text())
    for seed in SEEDS:
        windows={}
        for f in ready['families'][f'Whisper_{seed}']['files']:
            path=track(f['path']);assert sha(path)==f['sha256'];v=json.loads(path.read_text());windows.setdefault(v['recording_id'],[]).append(v)
        assert len(windows)==22
        for ws in windows.values():ws.sort(key=lambda v:v['window']);assert [v['window'] for v in ws]==[0,1]
        for ds,split in [('FLEURS','TEST'),('CV27','CV27')]:
            p=arrays(track(r/f'experiments/acceptors/inputs/{ds}_{seed}.npz'));d=arrays(track(r/f'experiments/extensions/numeric_inputs/{ds}_{seed}_diagnostics.npz'))
            old=arrays(track(root/f'artifacts/iscas_repetition_robustness/20261014_v146_matched_recovery/COUNTS_{ds}_{seed}.npz'))
            np.testing.assert_array_equal(old['lang'],p['lang']);np.testing.assert_array_equal(old['flags'],p['flags']);np.testing.assert_array_equal(old['NoAcquisition'],p['B']);np.testing.assert_array_equal(old['HFFallbackFixed'],p['S'])
            np.testing.assert_array_equal(p['ids'],d['ids']);where={str(u):i for i,u in enumerate(old['ids'])}
            nw=len(p['k']);cr=np.full(nw,np.nan);tok=cr.copy();rep=cr.copy();chars=np.zeros(nw,int);utf8=np.zeros(nw,int);nt=np.zeros(nw,int);terminations=Counter();seen=set()
            item=next(v for v in idx if v['seed']==seed and v['split']==split);src=Path(item['feature_input']['path']);h=hashlib.sha256()
            with src.open('rb') as stream:
                for line in stream:
                    h.update(line);v=json.loads(line);aid=hashlib.sha256(f"CSCWD_R1|{v['lang']}|{v['uid']}".encode()).hexdigest();assert aid not in seen;seen.add(aid);i=where[aid]
                    assert LANGS[int(p['lang'][i])]==v['lang'];ws=windows.get(aid,[v]) if ds=='FLEURS' else [v]
                    assert len(ws)==p['offsets'][i+1]-p['offsets'][i]
                    for j,b in enumerate(ws):
                        q=int(p['offsets'][i]+j);mapping=b.get('mapping',b.get('original_mapping'));top=next(m['unique_index'] for m in mapping if m['source']=='B5' and m['rank']==0);assert top==0
                        c=b['candidates'][top];text=c['text'];raw=text.encode('utf-8');cr[q]=len(raw)/len(zlib.compress(raw));chars[q]=len(text);utf8[q]=len(raw)
                        words=wer.words(text,v['lang']);grams=[tuple(words[k:k+4]) for k in range(max(0,len(words)-3))];freq=Counter(grams);rep[q]=sum(freq[g]>=3 for g in grams)/max(1,len(grams))
                        ids=list(c['token_ids']);termination=c['termination'];terminations[termination]+=1
                        assert termination in ['natural_eos','length_cap'],(ds,seed,q,termination)
                        if termination=='natural_eos':ids.append(eos)
                        assert len(ids)==c['raw_generated_tokens'];assert eos not in c['token_ids'];nt[q]=len(ids)
                        tokenbytes=b''.join(int(t).to_bytes(width,'little') for t in ids);tok[q]=len(tokenbytes)/len(zlib.compress(tokenbytes))
                        assert tok[q]==hf_ratio(np.array(ids,dtype=np.int64),cfg['vocab_size'])
            manifest[str(src)]={'sha256':h.hexdigest(),'bytes':src.stat().st_size};assert h.hexdigest()==item['feature_input']['sha256'];assert seen==set(where)
            assert np.isfinite(cr).all() and np.isfinite(tok).all();np.testing.assert_allclose(cr,d['cr_window'],atol=0,rtol=0)
            assert p['raw_observed'][:,0,3].all();np.testing.assert_allclose(rep,p['raw_features'][:,0,3],atol=0,rtol=0)
            z=np.zeros(len(p['ids']),bool);np.logical_or.at(z,p['window_owner'],cr>2.4);np.testing.assert_array_equal(z,p['flags'])
            dest=out/f'{ds}_{seed}_gate_features.npz';np.savez_compressed(dest,ids=p['ids'],window_owner=p['window_owner'],window_index=p['window_index'],cr_utf8=cr,cr_token_ids=tok,r43=rep,unicode_characters=chars,utf8_bytes=utf8,generated_token_count_with_eos=nt)
            checks.append({'dataset':ds,'checkpoint':seed,'recordings':len(p['ids']),'windows':nw,'raw_CR_exact':True,'raw_repetition_exact':True,'original_recording_flags_exact':True,'HF_function_exact_all_windows':True,'B_S_alignment_exact':True,'terminations':dict(terminations),'output_sha256':sha(dest)})
            print(json.dumps(checks[-1]),flush=True)
    save(out/'PRIVATE_SOURCE_RECEIPT.json',{'script_sha256':sha(__file__),'source_files':manifest,'checks':checks,'token_ratio':{'implementation':'transformers 4.57.6 WhisperGenerationMixin._retrieve_compression_ratio','vocab_size':cfg['vocab_size'],'token_byte_width':width,'endianness':'little','zlib_level':'default','eos_token_id':eos,'EOS_handling':'Restore exactly one EOS for cached natural_eos, none for length_cap; exclude decoder prefix and padding, matching HF pre-fallback seek_sequence.'},'scope':'Counterfactual outer gate on frozen original top beam; not the full HF internal retry/no-speech policy. Numeric exports contain no text, token IDs, audio or references. No new inference.'})
if __name__=='__main__':main()
