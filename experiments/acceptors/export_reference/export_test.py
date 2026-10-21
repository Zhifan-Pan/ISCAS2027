"""Read-only same-HF TEST bank export, including exact whole-recording scoring.

No fitting. Multiwindow alternatives are concatenated and scored as complete
recordings inside the private process. Only numeric alignments leave it.
"""
from study_common import *
import argparse, sqlite3, time

def run(seed):
    start=time.monotonic()
    dests=[R/'private'/f'{ds}_{seed}.npz' for ds in ['FLEURS','CV27']]
    assert not any(p.exists() for p in dests)
    old=load(P/'artifacts/asr_restructured/20260928_v1/evidence/CHECKPOINT_REPLAY_LOCK.json')
    index=load(P/'ASR_v2_CV27_run_20260919/review_strengthening_20260923/reproduction/config/CACHE_INDEX.json')
    full=P/'artifacts/asr_official_fullaudio/20260929_v1'
    ready=load(full/'results/FULL_AUDIO_BANKS_READY.json')
    assert sha(full/'private/FULL_REFERENCES.jsonl')==ready['full_reference_sha256']
    assert sha(full/'private/AUDIO_ONLY.jsonl')==ready['window_manifest_sha256']
    refs={r['anon_id']:r['reference'] for r in map(json.loads,(full/'private/FULL_REFERENCES.jsonl').open())}
    windows={};audios={r['anon_id']:r for r in map(json.loads,(full/'private/AUDIO_ONLY.jsonl').open())}
    for item in ready['families'][f'Whisper_{seed}']['files']:
        assert sha(item['path'])==item['sha256'];v=load(item['path'])
        assert v['audio_sha256']==audios[v['anon_id']]['audio_sha256']
        windows.setdefault(v['recording_id'],[]).append(v)
    assert len(windows)==22
    for aid,ws in windows.items():
        ws.sort(key=lambda v:v['window']);assert [v['window'] for v in ws]==[0,1]
        assert ws[0]['start_sample']==0 and ws[0]['end_sample']==ws[1]['start_sample']
        assert ws[1]['end_sample']==audios[ws[0]['anon_id']]['total_samples_16k']
    nr=A/('20261014_v154_native_rescore' if seed==101 else '20261014_v155_native_rescore_replication')
    lockpath=nr/('PREDICTION_LOCK.json' if seed==101 else f'PREDICTION_LOCK_{seed}.json')
    nlock=load(lockpath);sourcepath=nr/f'private/ALL_RECORDS_{seed}.jsonl'
    assert sha(sourcepath)==nlock['complete_input_sha256']
    native={v['anon_id']:v for v in map(json.loads,sourcepath.open())};assert len(native)==62179
    prior={}
    for path in (V/'predictions').glob('*.json'):
        z=load(path)
        if z['seed']==seed and z['split']!='DEV':prior[z['anon_id']]=(path,z)
    cfg=load(P/'artifacts/cscwd_round1/20260924_r1/config.json')
    db=sqlite3.connect(Path(cfg['pll_cache']).as_uri()+'?mode=ro',uri=True)
    db.execute('PRAGMA query_only=ON')
    pll_identity=P/'ASR_v2_CV27_run_20260919/review_strengthening_20260923/reproduction/config/PLL_IDENTITY.json'
    assert db.execute('select value from metadata where name="PLL_IDENTITY_SHA256"').fetchone()[0]==sha(pll_identity)
    beta=np.asarray(load(V/'SELECTOR_LOCK.json')[str(seed)]['raw_beta'])
    pcache={};receipts=[]
    for ds,split in [('FLEURS','TEST'),('CV27','CV27')]:
        entry=next(v for v in index if v['split']==split and v['seed']==seed)
        assert sha(entry['feature_input']['path'])==entry['feature_input']['sha256']
        numeric=old['caches'][f'{ds}_{seed}'];assert sha(numeric['path'])==numeric['sha256']
        p=arrays(numeric['path']);pindex={str(u):i for i,u in enumerate(p['ids'])}
        z=arrays(V/f'COUNTS_{ds}_{seed}.npz');refN=arrays(nr/f'COUNTS_{ds}_{seed}.npz')
        pub=W/'finalization/reviewer_artifact/main_test/cache/data'
        published=arrays(pub/f'COUNTS_{ds}_{seed}.npz');publishedN=arrays(pub/f'NATIVE_RESCORE_COUNTS_{ds}_{seed}.npz')
        for field in ['NoAcquisition','HFFallbackFixed','HFFallbackDirect','flags','lang']:
            np.testing.assert_array_equal(z[field],published[field])
        np.testing.assert_array_equal(refN['counts'],publishedN['counts'])
        np.testing.assert_array_equal(refN['ids'],z['ids'])
        if ds=='CV27':
            meta=arrays(P/'artifacts/asr_submission_fullcv27/20260928_v1/private/CV27_SEAMLESS.npz')
            refs.update({str(i):str(t) for i,t in zip(meta['ids'],meta['groups'])})
        n=len(z['ids']);where={str(u):i for i,u in enumerate(z['ids'])}
        nw=n+(22 if ds=='FLEURS' else 0)
        owner=np.repeat(np.arange(n),[2 if str(a) in windows else 1 for a in z['ids']])
        offsets=np.r_[0,np.cumsum(np.bincount(owner,minlength=n))]
        wi=np.concatenate([np.arange(offsets[i+1]-offsets[i]) for i in range(n)])
        k=np.zeros(nw,int);kb=np.zeros(nw,int);x=np.zeros((nw,6,4));raw=np.full_like(x,np.nan)
        cc=np.zeros((nw,6,4),np.int64);hfidx=np.zeros(nw,int)
        candidates=np.full((nw,6),'',dtype='U64');body=np.full((nw,6),-1,int);plltok=np.full_like(body,-1)
        picksB=np.zeros(nw,int);picksN=np.zeros(nw,int)
        B=np.zeros((n,4),np.int64);N=B.copy();S=B.copy();D=B.copy()
        multi_rows=[];multi_counts=[];multi_hashes=[];stats=Counter();max_drift=0.;missing=[];seen=set()
        provenance=R/'private'/f'{ds}_{seed}_source_inventory.jsonl'
        with provenance.open('x') as out:
            for v in map(json.loads,open(entry['feature_input']['path'])):
                aid=key(f"CSCWD_R1|{v['lang']}|{v['uid']}");assert aid in where and aid not in seen;seen.add(aid)
                i=where[aid];pi=pindex[aid];lang=v['lang'];assert LANGS[z['lang'][i]]==lang
                row=native[aid];assert row['seed']==seed
                ww=windows.get(aid,[v]);assert len(ww)==len(row['windows'])==offsets[i+1]-offsets[i]
                textbanks=[];hftexts=[];ps=[]
                for j,(b,w) in enumerate(zip(ww,row['windows'])):
                    q=int(offsets[i]+j);assert w['window']==j and w['anon_id']==aid
                    mapping=b.get('mapping',b.get('original_mapping'))
                    bi=sorted({int(m['unique_index']) for m in mapping if m['source']=='B5'});assert bi[0]==0
                    beam=[b['candidates'][u] for u in bi];norm=[wer.words(c['text'],lang) for c in beam]
                    assert len(norm)==len(set(map(tuple,norm)))
                    kb[q]=k[q]=len(bi);bx=np.asarray(b['features'])[bi][:,COLS] if aid in windows else p['x'][pi,bi][:,COLS]
                    x[q,:k[q]]=bx;assert np.array_equal(x[q,0],np.zeros(4))
                    for cidx,oldj in enumerate(bi):
                        c=beam[cidx]
                        if aid in windows:pl=b['pll'][oldj] if b.get('pll') is not None else None
                        else:
                            tk=key(c['text'])
                            if tk not in pcache:
                                got=db.execute('select pll,ntokens from texts where key=?',(tk,)).fetchone()
                                assert got is not None and got[0] is not None
                                pcache[tk]={'pll':got[0],'ntokens':got[1]}
                            pl=pcache[tk]
                        raw[q,cidx],body[q,cidx],plltok[q,cidx]=raw4(c,pl,lang)
                        candidates[q,cidx]=key(f'{aid}|{j}|B|{oldj}|'+c['text'])
                    nt=w['native_text'];normhf=wer.words(nt,lang);duplicate=normhf in norm
                    assert duplicate==(w['status']=='DUPLICATE_RETAIN_BEAM')
                    sourcehash=None
                    if not duplicate:
                        if w['status']=='REUSED_MATCHED_RAW_FEATURES':
                            path,pr=prior[aid];s=pr['windows'][j];h=s['sources']['HFFallback'];assert h['text']==nt
                            top=np.asarray(s['beam_features_abs'][0]);hr=np.asarray(h['features_abs']);sourcehash=sha(path)
                        else:
                            assert w['status']=='MISSING_NATIVE_FEATURES'
                            name='features/'+key(w['record_key'])+'.json';path=nr/name
                            sourcehash=sha(path);assert sourcehash==nlock['feature_hashes'][name]
                            f=load(path);assert not f['references_read'] and f['asr_generation_calls']==0 and f['record_key']==w['record_key']
                            assert key(f['output'])==f['output_sha256'];top=np.asarray(f['top_features']);hr=np.asarray(f['native_features'])
                        assert top.shape==hr.shape==(4,) and np.isfinite(top).all() and np.isfinite(hr).all()
                        if not np.isfinite(raw[q,0]).all():assert kb[q]==1;raw[q,0]=top;stats['top_anchor_reused']+=1
                        cidx=int(k[q]);raw[q,cidx]=hr;x[q,cidx]=hr-top;hfidx[q]=cidx;k[q]+=1
                        candidates[q,cidx]=key(f'{aid}|{j}|HF|'+nt);stats['novel_HF']+=1
                        texts=[c['text'] for c in beam]+[nt]
                    else:
                        hfidx[q]=norm.index(normhf);stats['duplicate_HF']+=1;texts=[c['text'] for c in beam]
                    if k[q]>1:
                        if not np.isfinite(raw[q,:k[q]]).all():missing.append(q)
                        else:
                            drift=float(np.abs(raw[q,:k[q]]-raw[q,0]-x[q,:k[q]]).max());max_drift=max(max_drift,drift)
                            assert drift<1e-4,('relative_drift',ds,seed,q,drift)
                    elif not np.isfinite(raw[q,0]).all():stats['unobserved_raw_F_singleton']+=1
                    picksB[q]=int(np.argmax(bx@beta));picksN[q]=int(np.argmax(x[q,:k[q]]@beta))
                    assert texts[picksB[q]]==w['beam_output']
                    if len(ww)==1:
                        for cidx,t in enumerate(texts):cc[q,cidx]=counts(refs[aid],t,lang)
                        np.testing.assert_array_equal(cc[q,:kb[q]],p['counts'][pi,bi])
                    textbanks.append(texts);hftexts.append(nt)
                    ps.append({'window':j,'status':w['status'],'feature_sha256':sourcehash,'audio_sha256':w['audio_sha256']})
                def score_at(choices):return counts(refs[aid],' '.join(textbanks[j][int(c)].strip() for j,c in enumerate(choices)).strip(),lang)
                sl=slice(offsets[i],offsets[i+1]);B[i]=score_at(picksB[sl]);N[i]=score_at(picksN[sl]);S[i]=N[i] if z['flags'][i] else B[i]
                D[i]=counts(refs[aid],' '.join(t.strip() for t in hftexts).strip(),lang) if z['flags'][i] else B[i]
                if len(ww)==2:
                    m=np.zeros((6,6,4),np.int64);mh=np.full((6,6),'',dtype='U64')
                    for c0 in range(len(textbanks[0])):
                        for c1 in range(len(textbanks[1])):
                            m[c0,c1]=score_at([c0,c1]);mh[c0,c1]=key(' '.join([textbanks[0][c0].strip(),textbanks[1][c1].strip()]).strip())
                    multi_rows.append(i);multi_counts.append(m);multi_hashes.append(mh)
                out.write(json.dumps({'id':str(published['ids'][i]),'windows':ps})+'\n')
                if len(seen)%10000==0:save(R/'audit'/f'test_progress_{seed}.json',{'corpus':ds,'rows':len(seen),'total':n,'elapsed_seconds':time.monotonic()-start})
        assert seen==set(where)
        for actual,expected in [(B,z['NoAcquisition']),(N,refN['counts']),(S,z['HFFallbackFixed']),(D,z['HFFallbackDirect'])]:np.testing.assert_array_equal(actual,expected)
        assert not missing,('missing_nontrivial_features',ds,seed,missing)
        outpath=R/'private'/f'{ds}_{seed}.npz'
        np.savez_compressed(outpath,ids=published['ids'],lang=z['lang'],window_owner=owner,window_index=wi,offsets=offsets,k=k,k_beam=kb,x=x,raw_features=raw,raw_observed=np.isfinite(raw),single_counts=cc,candidate_ids=candidates,body_tokens=body,pll_tokens=plltok,hf_index=hfidx,flags=z['flags'],B_pick=picksB,N_pick=picksN,B=B,N=N,S=S,Direct=D,multi_rows=np.array(multi_rows,int),multi_counts=np.asarray(multi_counts,dtype=np.int64).reshape(-1,6,6,4),multi_output_hashes=np.asarray(multi_hashes).reshape(-1,6,6))
        receipt={'corpus':ds,'seed':seed,'rows':n,'windows':nw,'long_recordings':len(multi_rows),'full_recording_scoring':True,'original_B_N_S_Direct_exact':True,'F_candidates':int(k.sum()),'B_candidates':int(kb.sum()),'raw_missing_in_multi_candidate_rows':missing,'max_raw_vs_frozen_relative_drift':max_drift,'stats':dict(stats),'input_feature':entry['feature_input'],'original_numeric_input':numeric,'native_lock_sha256':sha(lockpath),'export_sha256':sha(outpath),'provenance_sha256':sha(provenance),'new_model_forward':False,'elapsed_seconds':time.monotonic()-start}
        save(R/'audit'/f'{ds}_{seed}.json',receipt);receipts.append(receipt);print(json.dumps(receipt),flush=True)
    return receipts

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int,choices=SEEDS,required=True);run(p.parse_args().seed)
