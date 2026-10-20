"""Only edit-gap weights change relative to the original HR4 objective."""
from common import *
from scipy.optimize import minimize
import scipy, time
from objective_engine import Prepared,scale_from_training,choose

class WeightedPairs(Prepared):
    def __init__(self,x,k,counts,languages,columns,scale,kind='rank'):
        super().__init__(x,k,counts,languages,columns,scale,'rank')
        error=counts[:,:,:3].sum(2);gaps=[]
        for a in range(x.shape[1]):
            for b in range(a+1,x.shape[1]):
                ix=np.flatnonzero((k>b)&(error[:,a]!=error[:,b]))
                gaps.append(np.abs(error[ix,b]-error[ix,a]))
        gap=np.concatenate(gaps).astype(float)
        assert len(gap)==len(self.pair_weight) and (gap>0).all()
        self.original_weight_sum=float(self.pair_weight.sum())
        self.c_train=float(self.pair_weight@gap/self.pair_weight.sum())
        self.pair_weight=self.pair_weight*gap/self.c_train
        np.testing.assert_allclose(self.pair_weight.sum(),self.original_weight_sum,rtol=1e-14,atol=1e-14)

def test():
    # Independent explicit pair enumeration tests orientation, weights and gradient.
    rng=np.random.default_rng(31);x=rng.normal(size=(10,6,4));x[:,0]=0
    k=np.array([1,2,3,4,5,6,2,3,4,5]);c=np.zeros((10,6,4),int)
    c[:,:,0]=rng.integers(0,9,size=(10,6));c[:,:,3]=13
    lang=np.arange(10)%5;scale=np.ones(4);d=WeightedPairs(x,k,c,lang,list(range(4)),scale)
    theta=np.array([.1,-.2,.07,.03]);pen=.013
    terms=[]
    for i in range(10):
        pairs=[(a,b) for a in range(k[i]) for b in range(a+1,k[i]) if c[i,a,0]!=c[i,b,0]]
        for a,b in pairs:
            gap=abs(c[i,b,0]-c[i,a,0]);direction=np.sign(c[i,b,0]-c[i,a,0]);w=1/(5*26*len(pairs))
            terms.append((w,gap,(x[i,a]-x[i,b])*direction))
    cm=sum(w*g for w,g,_ in terms)/sum(w for w,_,_ in terms)
    value=sum(w*g/cm*np.logaddexp(0,-theta@v) for w,g,v in terms)+pen*(theta@theta)
    np.testing.assert_allclose(value,d.value_grad(theta,pen)[0],rtol=1e-14,atol=1e-14)
    eps=1e-6;eye=np.eye(4)*eps
    fd=np.array([(d.value_grad(theta+v,pen)[0]-d.value_grad(theta-v,pen)[0])/(2*eps) for v in eye])
    np.testing.assert_allclose(fd,d.value_grad(theta,pen)[1],rtol=1e-7,atol=1e-8)
    return {'explicit_objective':True,'finite_difference_gradient':True,'singleton_no_pair':bool(d.pair_bank_counts[0]==0)}

def run(seed):
    start=time.monotonic();plan=load(R/'protocols/LOCKED_PLAN.json');path=A/f'acceptors/inputs/DEV_{seed}.npz'
    assert sha(path)==plan['DEV_inputs'][str(seed)]
    p=arrays(path);out=R/f'cv/HWR4_{seed}';out.mkdir(exist_ok=False)
    lambdas=plan['E03']['lambdas'];oof=np.full((49,len(p['ids'])),-1,np.int16);logs=[];folds=[]
    # Exact component/fold preservation; no TEST input is loaded by this script.
    for l in range(5):
        for group in np.unique(p['components'][p['lang']==l]):
            ix=(p['lang']==l)&(p['components']==group)
            assert len(np.unique(p['fold'][ix]))==1
    def fit(d,li,fold):
        opt=minimize(d.value_grad,np.zeros(4),args=(lambdas[li],),jac=True,method='L-BFGS-B',options=plan['E03']['optimizer']['options'])
        info=dict(fold=fold,lambda_index=li,penalty=lambdas[li],success=bool(opt.success),status=int(opt.status),message=str(opt.message),iterations=int(opt.nit),evaluations=int(opt.nfev),objective=float(opt.fun),gradient_max=float(np.max(np.abs(opt.jac))),theta=opt.x.tolist(),c_train=d.c_train)
        logs.append(info)
        with (out/'fit_log.jsonl').open('a') as f:f.write(json.dumps(info)+'\n')
        if not(opt.success and np.isfinite(opt.fun) and np.isfinite(opt.x).all()):
            save(out/'FAILED.json',info);raise RuntimeError(info)
        return opt.x
    for fold in range(5):
        tr=p['fold']!=fold;va=~tr;s=scale_from_training(p['x'],p['k'],tr,list(range(4)))
        d=WeightedPairs(p['x'][tr],p['k'][tr],p['counts'][tr],p['lang'][tr],list(range(4)),s)
        folds.append(dict(fold=fold,train=int(tr.sum()),held=int(va.sum()),scale=s.tolist(),c_train=d.c_train,pairs=len(d.pair_weight),original_pair_weight_sum=d.original_weight_sum))
        for li in range(49):
            theta=fit(d,li,fold);oof[li,va]=choose(p['x'][va],p['k'][va],list(range(4)),theta/s)
    metrics=[macro(p['counts'][np.arange(len(p['ids'])),oof[i]],p['lang']) for i in range(49)]
    selected=min(range(49),key=lambda i:(metrics[i],-lambdas[i]))
    s=scale_from_training(p['x'],p['k'],np.ones(len(p['ids']),bool),list(range(4)))
    d=WeightedPairs(p['x'],p['k'],p['counts'],p['lang'],list(range(4)),s);theta=fit(d,selected,'ALL_DEV')
    model=dict(family='HWR4',seed=seed,columns=list(range(4)),raw_beta=(theta/s).tolist(),theta=theta.tolist(),scale=s.tolist(),c_train=d.c_train,lambda_index=selected,penalty=lambdas[selected],selected_OOF_WER=metrics[selected],plan_sha256=sha(R/'protocols/LOCKED_PLAN.json'),input_sha256=sha(path),locked_utc=utc(),scope='retrospective; no original confirmation identity')
    save(R/f'models/HWR4_{seed}.json',model);np.savez_compressed(out/'oof_picks.npz',picks=oof)
    save(out/'RESULT.json',dict(folds=folds,grid=[dict(penalty=v,OOF_WER=metrics[i]) for i,v in enumerate(lambdas)],selected_index=selected,converged_fits=sum(l['success'] for l in logs),expected_fits=246,elapsed_seconds=time.monotonic()-start,environment=dict(python=sys.version,numpy=np.__version__,scipy=scipy.__version__)))
    print(json.dumps(dict(seed=seed,complete=True,elapsed_seconds=time.monotonic()-start,selected=selected)),flush=True)
if __name__=='__main__':
    save(R/'validation/HWR4_objective_tests.json',test())
    for seed in SEEDS:run(seed)
    save(R/'models/HWR4_LOCK.json',dict(locked_utc=utc(),models={f'HWR4_{s}.json':sha(R/f'models/HWR4_{s}.json') for s in SEEDS},scope='DEV-only selection before TEST evaluation'))
