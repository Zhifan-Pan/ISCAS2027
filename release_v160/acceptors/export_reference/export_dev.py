"""Read-only full DEV candidate export. No model loading or fitting.

Original frozen relative features and observed absolute values are stored
separately. Unobserved singleton raw scores are explicit NaNs. They are not
treated as zero PLL/decoder observations.
"""
from study_common import *
import argparse, csv, time

def run(seed):
    start=time.monotonic();out=R/'private'/f'DEV_{seed}.npz'
    assert not out.exists()
    md=load(V/'DATA_SOURCES.json')[str(seed)]
    assert sha(md['dev_npz'])==md['dev_sha256']
    p=arrays(md['dev_npz']);g=arrays(F/str(seed)/'DEV_FEATURES.npz')
    inherited=arrays(R8/f'reviewer_artifact/r8/inputs/dev/DEV_{seed}.npz')
    beta_lock=load(V/'SELECTOR_LOCK.json')[str(seed)];assert beta_lock['columns']==COLS
    beta=np.asarray(beta_lock['raw_beta']);n=len(p['ids'])
    np.testing.assert_array_equal(p['ids'],g['ids']);np.testing.assert_array_equal(p['lang'],g['lang'])
    np.testing.assert_array_equal(inherited['ids'],np.array([key('R8-DEV|'+str(x)) for x in p['ids']]))
    np.testing.assert_array_equal(g['fold'],inherited['fold'])
    assert n==58171 and (p['duration']<=30).all()
    for l,component in set(zip(p['lang'].tolist(),inherited['components'].tolist())):
        mask=(p['lang']==l)&(inherited['components']==component)
        assert len(np.unique(g['fold'][mask]))==1,('fold_crossing',seed,l,component)
    references={v['anon_id']:v['reference'] for v in map(json.loads,(P/'artifacts/asr_official_splits/20260929_v1/private/DEV_LABELS.jsonl').open())}
    cached={v['index']:v for v in load(R8/f'prepared/acquisition/cached_{seed}.json')}
    repairs={(v['seed'],v['index']):v for v in load(R8/'audit/canonical_dev_banks/RESULT.json')['corrected_source_map']}
    identity={int(v['index']):v for v in csv.DictReader((R8/'generated/hf_dev_labels/source_identity.csv').open()) if int(v['seed'])==seed}
    assert len(identity)==n
    k=np.zeros(n,int);kb=np.zeros(n,int);x=np.zeros((n,6,4));raw=np.full((n,6,4),np.nan)
    cc=np.zeros((n,6,4),np.int64);candids=np.full((n,6),'',dtype='U64')
    body=np.full((n,6),-1,np.int64);pll_tokens=np.full((n,6),-1,np.int64)
    hf_index=np.zeros(n,int);bp=np.zeros(n,int);npick=np.zeros(n,int)
    stats=Counter();max_drift=0.;raw_multi_missing=[]
    inventory=R/'private'/f'DEV_{seed}_source_inventory.jsonl'
    with inventory.open('x') as log:
        for i in range(n):
            aid=str(p['ids'][i]);lang=LANGS[int(p['lang'][i])]
            cpath=Path(md['candidates'])/f'{i:05d}.json'
            if (seed,i) in repairs:cpath=Path(repairs[(seed,i)]['effective']['path'])
            c=load(cpath);assert c['anon_id']==aid and c['lang']==lang
            bi=sorted({int(m['unique_index']) for m in c['mapping'] if m['source']=='B5'})
            assert bi==np.flatnonzero(g['bm'][i]).tolist() and bi[0]==0
            beam=[c['candidates'][j] for j in bi];norm=[wer.words(b['text'],lang) for b in beam]
            kb[i]=len(bi);k[i]=len(bi);x[i,:k[i]]=p['x'][i,bi][:,COLS];cc[i,:k[i]]=p['counts'][i,bi]
            assert np.array_equal(x[i,0],np.zeros(4))
            for j,oldj in enumerate(bi):
                pl=c['pll'][oldj] if c.get('pll') is not None else None
                raw[i,j],body[i,j],pll_tokens[i,j]=raw4(beam[j],pl,lang)
                candids[i,j]=key(f'{aid}|0|B|{oldj}|'+beam[j]['text'])
            if i in cached:
                spath=V/'predictions'/cached[i]['source_record'];z=load(spath)
                assert z['seed']==seed and z['anon_id']==aid and z['window_count']==1 and not z['references_read']
                sw=z['windows'][0];s=sw['sources']['HFFallback'];text=s['text'];duplicate=s['duplicates_beam']
                observed_beam=np.asarray(sw['beam_features_abs']);hfraw=np.asarray(s['features_abs'])
                top=observed_beam[0]
                assert [b['text'] for b in beam]==[b['text'] for b in sw['beam']]
                token_source='historical_HF';rng_verified='inherited source lock'
            else:
                spath=R8/f'private/hf_dev/{seed}/{i:05d}.json';z=load(spath)
                assert z['seed']==seed and z['index']==i and z['anon_id']==aid and z['source']=='HFFallback'
                assert z['candidate_sha256']==sha(cpath) and not z['references_read']
                assert z['window_count']==1 and z['audio_sha256']==c['audio_sha256']
                text=z['source_text'];duplicate=z['duplicates_beam'];hfraw=z['source_features'];top=z['top_features']
                token_source='R8_real_HF';rng_verified={'hash':z['rng_label_sha256'],'seed':z['rng_seed']}
            source_hash=sha(spath);assert source_hash==identity[i]['source_sha256']
            actual_duplicate=wer.words(text,lang) in norm;assert duplicate==actual_duplicate
            if not duplicate:
                hfraw=np.asarray(hfraw,float);top=np.asarray(top,float)
                assert hfraw.shape==top.shape==(4,) and np.isfinite(hfraw).all() and np.isfinite(top).all()
                # A formerly singleton B has a genuine measured anchor when F expands.
                if not np.isfinite(raw[i,0]).all():
                    assert kb[i]==1;raw[i,0]=top;stats['top_anchor_reused']+=1
                j=int(k[i]);x[i,j]=hfraw-top;raw[i,j]=hfraw
                cc[i,j]=counts(references[aid],text,lang);candids[i,j]=key(f'{aid}|0|HF|'+text)
                hf_index[i]=j;k[i]+=1;stats['novel_HF']+=1
            else:
                hf_index[i]=norm.index(wer.words(text,lang));stats['duplicate_HF']+=1
            if k[i]>1:
                if not np.isfinite(raw[i,:k[i]]).all():raw_multi_missing.append(i)
                else:
                    drift=float(np.abs(raw[i,:k[i]]-raw[i,0]-x[i,:k[i]]).max())
                    max_drift=max(max_drift,drift);assert drift<1e-4,('raw_relative_drift',seed,i,drift)
            elif not np.isfinite(raw[i,0]).all():stats['unobserved_raw_F_singleton']+=1
            assert (cc[i,:k[i],3]==cc[i,0,3]).all()
            # Same genuine candidate references; no training label inferred from a chosen count.
            bp[i]=int(np.argmax(x[i,:kb[i]]@beta));npick[i]=int(np.argmax(x[i,:k[i]]@beta))
            np.testing.assert_array_equal(cc[i,bp[i]],inherited['B'][i])
            np.testing.assert_array_equal(cc[i,npick[i]],inherited['NplusR'][i])
            log.write(json.dumps({'index':i,'id':str(inherited['ids'][i]),'candidate_path':str(cpath),'candidate_sha256':sha(cpath),'source_path':str(spath),'source_sha256':source_hash,'source':token_source,'rng':rng_verified})+'\n')
            if (i+1)%10000==0:save(R/'audit'/f'dev_progress_{seed}.json',{'rows':i+1,'total':n,'elapsed_seconds':time.monotonic()-start})
    flags=np.load(V/f'DEV_FLAGS_{seed}.npy',allow_pickle=False)
    np.savez_compressed(out,ids=inherited['ids'],lang=p['lang'],fold=g['fold'],components=inherited['components'],k=k,k_beam=kb,x=x,raw_features=raw,raw_observed=np.isfinite(raw),counts=cc,candidate_ids=candids,body_tokens=body,pll_tokens=pll_tokens,hf_index=hf_index,flags=flags,B_pick=bp,N_pick=npick)
    receipt={'seed':seed,'rows':n,'windows':n,'F_candidates':int(k.sum()),'B_candidates':int(kb.sum()),'all_B_N_counts_reconstructed':True,'fold_components_crossing':0,'raw_missing_in_multi_candidate_rows':raw_multi_missing,'stats':dict(stats),'max_raw_vs_frozen_relative_drift':max_drift,'raw_unknown_policy':'NaN with observed mask. Stored frozen x is genuine top-relative data. Singleton x-x is not a claim that raw f=0. No fitting has occurred.','source_inventory_sha256':sha(inventory),'export_sha256':sha(out),'elapsed_seconds':time.monotonic()-start,'new_model_forward':False}
    save(R/'audit'/f'DEV_{seed}.json',receipt);print(json.dumps(receipt),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int,choices=SEEDS,required=True);run(p.parse_args().seed)
