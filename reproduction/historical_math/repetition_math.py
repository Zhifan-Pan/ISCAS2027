"""Shared candidate scoring and dimension-generalized, unchanged fitting losses."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
os.environ['CUDA_VISIBLE_DEVICES']=''
import numpy as np
from scipy.optimize import minimize,check_grad
import selector_math_full as sm
import selection_core as core
from fit_review_controls import objective as risk_loss
from fit_objective_validation import loss as pair_loss
from fit_matched_controls import grid,reduce_design

def prepared(p,cols,kind):
    scale=sm.design(p,np.ones(len(p['k']),int),cols)[2]
    error=p['counts'][:,:,:3].sum(2)
    den=np.bincount(p['lang'],weights=p['counts'][:,0,3],minlength=5)
    assert (den>0).all()
    if kind=='risk':
        x=np.ascontiguousarray(p['x'][:,:,cols]/scale)
        cost=(error-error[:,:1]).astype(float)
        weight=1/(5*den[p['lang']]);valid=np.arange(6)[None,:]<p['k'][:,None]
        return (x,cost,weight,valid),scale
    pairs=[];number=np.zeros(len(p['k']),int)
    for a in range(6):
        for b in range(a+1,6):
            ix=np.flatnonzero((p['k']>b)&(error[:,a]!=error[:,b]));number[ix]+=1
            sign=np.sign(error[ix,b]-error[ix,a])
            x=(p['x'][ix,a][:,cols]-p['x'][ix,b][:,cols])*sign[:,None]/scale
            pairs.append((ix,x))
    ix=np.concatenate([a for a,x in pairs]);x=np.ascontiguousarray(np.concatenate([x for a,x in pairs]))
    assert len(ix)
    weight=1/(den[p['lang'][ix]]*number[ix]);weight/=weight.sum()
    return (x,weight),scale

def solve(data,cols,kind,lam,options):
    args,scale=data;loss=risk_loss if kind=='risk' else pair_loss
    opt=minimize(loss,np.zeros(len(cols)),args=(*args,lam),jac=True,method='L-BFGS-B',options=options)
    if not (opt.success and np.isfinite(opt.fun) and np.isfinite(opt.x).all()):
        raise RuntimeError(str(dict(kind=kind,columns=cols,penalty=lam,status=int(opt.status),message=str(opt.message),iterations=int(opt.nit),objective=float(opt.fun))))
    model=dict(columns=list(cols),raw_beta=(opt.x/scale).tolist(),theta=opt.x.tolist(),scale=scale.tolist(),lambda_value=float(lam))
    info=dict(converged=bool(opt.success),iterations=int(opt.nit),evaluations=int(opt.nfev),objective=float(opt.fun),gradient_max=float(abs(opt.jac).max()))
    return model,info

def fit_grids(p,specs,cfg,selected=None):
    models={};logs=[];draws=None;parent=None
    options={k:cfg['optimizer'][k] for k in ['maxiter','ftol','gtol','maxls']}
    for name,spec in specs.items():
        cols=tuple(spec['columns']);kind=spec['objective']
        indexes=list(range(49)) if selected is None else [selected[name]]
        if kind.startswith('ridge'):
            if kind=='ridge_b20':
                if draws is None:draws=sm.prepare(p,core.COLS,'Recording-B20',cfg['bag_seeds'])
                ds=reduce_design(draws,cols)
            else:
                if parent is None:parent=[sm.design(p,np.ones(len(p['k']),int),core.COLS)]
                ds=reduce_design(parent,cols)
            models[name]=grid(ds,cols,[cfg['lambdas'][j] for j in indexes])
        elif kind=='fusion':
            scale=sm.design(p,np.ones(len(p['k']),int),cols)[2]
            ag=[(a,g) for a in cfg['fusion_alphas'] for g in cfg['fusion_gammas']]
            models[name]=[dict(columns=list(cols),raw_beta=(np.array([1.,*ag[j]])/scale).tolist(),scale=scale.tolist(),alpha=ag[j][0],gamma=ag[j][1]) for j in indexes]
        else:
            data=prepared(p,cols,kind);models[name]=[]
            for j in indexes:
                model,info=solve(data,cols,kind,cfg['lambdas'][j],options)
                models[name].append(model);logs.append(dict(method=name,index=j,**info))
    return models,logs

def choose(p,model):
    if not model.get('repetition_guard',False):return sm.choose(p,model)
    # Beam is included (zero relative features); padding and repetition-increasing
    # alternatives are excluded without looking at any reference or language.
    scores=p['x'][:,:,model['columns']]@np.asarray(model['raw_beta'])
    valid=(np.arange(6)[None,:]<p['k'][:,None])&(p['x'][:,:,4]<=0)
    assert valid[:,0].all()
    scores[~valid]=-np.inf;j=scores.argmax(1);best=scores[np.arange(len(j)),j]
    top=np.sort(scores,axis=1)
    near=(p['k']>1)&((abs(best)<1e-10)|(abs(top[:,-1]-top[:,-2])<1e-10))
    for i in np.flatnonzero(near):
        v=p['x'][i,:int(p['k'][i])][:,model['columns']]@np.asarray(model['raw_beta'])
        v[~valid[i,:int(p['k'][i])]]=-np.inf;j[i]=v.argmax();best[i]=v[j[i]]
    out=np.where(best>0,j,0)
    assert valid[np.arange(len(out)),out].all()
    return out

def checks():
    rng=np.random.default_rng(20261002);checks=[]
    for d in [4,8,9]:
        x=rng.normal(size=(17,6,d));x[:,0]=0;valid=np.arange(6)[None,:]<rng.integers(1,7,(17,1))
        cost=rng.normal(size=(17,6));w=rng.random(17);w/=w.sum();theta=rng.normal(size=d)
        err=check_grad(lambda t:risk_loss(t,x,cost,w,valid,.03)[0],lambda t:risk_loss(t,x,cost,w,valid,.03)[1],theta)
        assert err<1e-6,err
        px=rng.normal(size=(31,d));pw=rng.random(31);pw/=pw.sum()
        pe=check_grad(lambda t:pair_loss(t,px,pw,.03)[0],lambda t:pair_loss(t,px,pw,.03)[1],theta)
        assert pe<1e-6,pe
        checks.append(dict(dimensions=d,risk_gradient_error=float(err),pair_gradient_error=float(pe)))
    p={'x':np.zeros((4,6,11)), 'k':np.array([3,2,1,2])}
    p['x'][0,1,0]=2;p['x'][0,1,4]=.1;p['x'][0,2,0]=1
    p['x'][1,1,0]=2;p['x'][1,1,4]=0
    p['x'][3,1,0]=2;p['x'][3,1,4]=-.1
    model={'columns':[0],'raw_beta':[1.],'repetition_guard':True}
    np.testing.assert_array_equal(choose(p,model),[2,1,0,1])
    return dict(gradients=checks,guard_checks='Reject increasing repetition; retain feasible winner; singleton and zero-margin ties keep Beam.')
