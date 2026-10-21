"""Complete frozen 49-lambda, five-component-fold acceptor CV; DEV only."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
import argparse,datetime,hashlib,json,time,platform,sys
from pathlib import Path
import numpy as np
import scipy
from scipy.optimize import minimize
from objective_engine import Prepared,scale_from_training,choose

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()
def save(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix('.tmp')
    t.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n');t.replace(p)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def macro(c,l):return float(np.mean([100*c[l==j,:3].sum()/c[l==j,3].sum() for j in range(5)]))

def run(root,data_root,seed,family):
    start=time.monotonic();planpath=root/'prerefit_plan.json';plan=json.loads(planpath.read_text())
    assert plan['status']=='LOCKED_BEFORE_NEW_CV' and family in ['H4','HR4','H3']
    data=data_root/f'DEV_{seed}.npz';assert sha(data)==plan['DEV_input_sha256'][str(seed)]
    assert sha(__file__)==plan['code_sha256']['fit_acceptor.py']
    assert sha(Path(__file__).with_name('objective_engine.py'))==plan['code_sha256']['objective_engine.py']
    out=root/'cv'/f'{family}_{seed}';out.mkdir(exist_ok=False)
    with np.load(data,allow_pickle=False) as z:p={k:z[k].copy() for k in ['x','k','counts','lang','fold','components']}
    cols=[0,2,3] if family=='H3' else [0,1,2,3];kind='rank' if family=='HR4' else 'risk'
    n=len(p['k']);oof=np.full((49,n),-1,np.int16);logs=[];folddata=[];lambdas=plan['lambdas']
    assert len(lambdas)==49 and set(p['fold'])==set(range(5))
    for lang in range(5):
        for c in np.unique(p['components'][p['lang']==lang]):
            assert len(np.unique(p['fold'][(p['lang']==lang)&(p['components']==c)]))==1
    def fit(data,li,fold):
        penalty=lambdas[li];options=plan['optimizer']['options']
        opt=minimize(data.value_grad,np.zeros(len(cols)),args=(penalty,),jac=True,method='L-BFGS-B',options=options)
        info={'fold':fold,'lambda_index':li,'lambda':penalty,'success':bool(opt.success),'status':int(opt.status),'message':str(opt.message),'iterations':int(opt.nit),'evaluations':int(opt.nfev),'objective':float(opt.fun),'gradient_max':float(np.max(np.abs(opt.jac))),'theta':opt.x.tolist()}
        logs.append(info)
        with (out/'fit_log.jsonl').open('a') as f:f.write(json.dumps(info)+'\n')
        if not(opt.success and np.isfinite(opt.fun) and np.isfinite(opt.x).all()):
            save(out/'FAILED.json',info);raise RuntimeError(f'{family}/{seed}/{fold}/{li} failed; see fit_log.jsonl')
        return opt.x,info
    for fold in range(5):
        tr=p['fold']!=fold;va=~tr;scale=scale_from_training(p['x'],p['k'],tr,cols)
        d=Prepared(p['x'][tr],p['k'][tr],p['counts'][tr],p['lang'][tr],cols,scale,kind)
        errs=p['counts'][tr,:,:3].sum(2);valid=np.arange(6)[None,:]<p['k'][tr,None]
        delta=errs-errs[:,:1]
        fd={'fold':fold,'train_recordings':int(tr.sum()),'held_recordings':int(va.sum()),'scale':scale.tolist(),'train_reference_words_by_language':[int(p['counts'][tr&(p['lang']==l),0,3].sum()) for l in range(5)],'non_top_labels':{'better_than_top':int(((delta<0)&valid).sum()),'worse_than_top':int(((delta>0)&valid).sum()),'equal_to_top':int(((delta==0)&valid&(np.arange(6)[None,:]>0)).sum())}}
        if kind=='rank':fd.update(valid_pairs=int(len(d.pair_weight)),banks_with_pairs=int((d.pair_bank_counts>0).sum()),sum_pair_weights=float(d.pair_weight.sum()))
        folddata.append(fd)
        for li in range(49):
            theta,info=fit(d,li,fold)
            oof[li,va]=choose(p['x'][va],p['k'][va],cols,theta/scale)
            if li%8==0:save(out/'progress.json',{'pid':os.getpid(),'family':family,'seed':seed,'fold':fold,'lambda_index':li,'elapsed_seconds':time.monotonic()-start})
    assert (oof>=0).all() and (oof<p['k'][None,:]).all()
    metrics=[macro(p['counts'][np.arange(n),oof[li]],p['lang']) for li in range(49)]
    selected=min(range(49),key=lambda li:(metrics[li],-lambdas[li]))
    scale=scale_from_training(p['x'],p['k'],np.ones(n,bool),cols)
    data=Prepared(p['x'],p['k'],p['counts'],p['lang'],cols,scale,kind)
    theta,final=fit(data,selected,'ALL_DEV');model={'family':family,'seed':seed,'columns':cols,'objective':kind,'theta':theta.tolist(),'scale':scale.tolist(),'raw_beta':(theta/scale).tolist(),'lambda_index':selected,'lambda':lambdas[selected],'plan_sha256':sha(planpath),'input_sha256':sha(data_root/f'DEV_{seed}.npz'),'selected_OOF_macro_WER':metrics[selected],'final_fit':final,'scope':'retrospective full-HF-expanded DEV fit; no new confirmation','locked_utc':utc()}
    save(root/'models'/f'{family}_{seed}.json',model)
    np.savez_compressed(out/'oof_picks.npz',picks=oof)
    save(out/'RESULT.json',{'family':family,'seed':seed,'grid':[{'lambda_index':i,'lambda':lambdas[i],'OOF_macro_WER':metrics[i]} for i in range(49)],'selected_index':selected,'folds':folddata,'converged_fits':sum(v['success'] for v in logs),'expected_fits':246,'elapsed_seconds':time.monotonic()-start,'environment':{'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'platform':platform.platform()},'model_sha256':sha(root/'models'/f'{family}_{seed}.json')})
    print(json.dumps({'family':family,'seed':seed,'complete':True,'fits':len(logs),'selected_index':selected,'OOF_macro_WER':metrics[selected],'elapsed_seconds':time.monotonic()-start}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--data-root',type=Path,required=True);p.add_argument('--seed',type=int,choices=[101,202,303],required=True);p.add_argument('--family',choices=['H4','HR4','H3'],required=True)
    a=p.parse_args();run(a.root.resolve(),a.data_root.resolve(),a.seed,a.family)
