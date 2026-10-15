"""Full-pool implementation of the frozen ridge math; identical ordering/RNG.

Avoid a full text-string scan per bootstrap group and Python candidate-row lists.
The original implementation remains immutable as the numerical parity oracle.
"""
import numpy as np
from selector_math import subset,fit,choose,selected_counts,macro


def design(p,mult,cols):
    den=np.bincount(p['lang'],weights=mult*p['counts'][:,0,3],minlength=5)
    if np.any(den<=0):raise ValueError('Empty language')
    k=p['k'].astype(int)-1
    keep=(np.arange(p['x'].shape[1]-1)[None,:]<k[:,None])&(mult[:,None]>0)
    row=np.broadcast_to(np.arange(len(k))[:,None],keep.shape)[keep]
    if not len(row):raise ValueError('No nonbeam fitting rows')
    x=np.ascontiguousarray(p['x'][:,1:][:,:,cols][keep],dtype=float)
    e=p['counts'][:,:,:3].sum(2)
    y=np.asarray((e[:,:1]-e[:,1:])[keep],float)
    w=np.asarray(mult[row]/(den[p['lang'][row]]*k[row]),float);w/=w.sum()
    s=np.sqrt((w[:,None]*x*x).sum(0));s=np.where(s>1e-12,s,1.)
    z=x/s
    return z.T@(w[:,None]*z),z.T@(w*y),s


def multiplicity(p,seed,group=False):
    rng=np.random.default_rng(seed);out=np.zeros(len(p['k']),int)
    for lang in range(5):
        ix=np.flatnonzero(p['lang']==lang)
        if group:
            labels,inverse=np.unique(p['groups'][ix],return_inverse=True)
            m=np.bincount(rng.integers(len(labels),size=len(labels)),minlength=len(labels))
            out[ix]=m[inverse]
        else:
            out+=np.bincount(ix[rng.integers(len(ix),size=len(ix))],minlength=len(out))
    return out


def prepare(p,cols,family,seeds):
    draws=[np.ones(len(p['k']),int)] if family=='Single' else [multiplicity(p,s,family=='Group-B20') for s in seeds]
    return [design(p,m,cols) for m in draws]


def fusion(p,alpha,gamma):
    _,_,s=design(p,np.ones(len(p['k']),int),(0,10,2))
    return {'columns':[0,10,2],'raw_beta':(np.asarray([1,alpha,gamma])/s).tolist(),
            'alpha':float(alpha),'gamma':float(gamma),'scale':s.tolist()}
