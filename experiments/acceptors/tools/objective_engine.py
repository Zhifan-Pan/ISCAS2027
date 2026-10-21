"""Prepared float64 versions of the supplied risk and RankNet objectives.

The rank objective uses 1/(L*N_language*pair_count), without renormalizing
pair weights to sum to one. This is a new instance, not historical RankNet.
"""
import numpy as np

def scale_from_training(x,k,train,columns):
    x=np.asarray(x,dtype=np.float64)[:,:,columns]
    valid=(np.arange(x.shape[1])[None,:]<k[:,None]) & (np.arange(x.shape[1])[None,:]>0) & train[:,None]
    scale=np.sqrt(np.mean(x[valid]**2,axis=0)) if valid.any() else np.ones(len(columns))
    scale=np.where(scale<1e-12,1.,scale)
    assert np.isfinite(scale).all()
    return scale

class Prepared:
    def __init__(self,x,k,counts,languages,columns,scale,kind):
        self.kind=kind
        valid=np.arange(x.shape[1])[None,:]<k[:,None]
        self.offsets=np.r_[0,np.cumsum(k)]
        self.owner=np.repeat(np.arange(len(k)),k)
        self.x=np.ascontiguousarray((x[:,:,columns]/scale)[valid],dtype=np.float64)
        self.edits=counts[:,:,:3].sum(2)[valid].astype(np.float64)
        langs=np.unique(languages);den={int(l):counts[languages==l,0,3].sum() for l in langs}
        assert all(v>0 for v in den.values())
        self.weight=np.array([1/(len(langs)*den[int(l)]) for l in languages])
        assert np.isfinite(self.x).all()
        if kind=='rank':
            error=counts[:,:,:3].sum(2);pairs=[];number=np.zeros(len(k),int)
            for a in range(x.shape[1]):
                for b in range(a+1,x.shape[1]):
                    ix=np.flatnonzero((k>b)&(error[:,a]!=error[:,b]));number[ix]+=1
                    sign=np.sign(error[ix,b]-error[ix,a])
                    differences=(x[ix,a][:,columns]-x[ix,b][:,columns])*sign[:,None]/scale
                    pairs.append((ix,differences))
            ix=np.concatenate([v[0] for v in pairs]);self.d=np.ascontiguousarray(np.concatenate([v[1] for v in pairs]))
            self.pair_weight=self.weight[ix]/number[ix]
            self.pair_bank_counts=number
    def value_grad(self,theta,penalty):
        if self.kind=='rank':
            margin=self.d@theta
            value=float(self.pair_weight@np.logaddexp(0.,-margin)+penalty*(theta@theta))
            gradient=-(self.d.T@(self.pair_weight*np.exp(-np.logaddexp(0.,margin))))+2*penalty*theta
        else:
            s=self.x@theta;starts=self.offsets[:-1]
            maxima=np.maximum.reduceat(s,starts);mass=np.exp(s-maxima[self.owner])
            mass/=np.add.reduceat(mass,starts)[self.owner]
            mean=np.add.reduceat(mass*self.edits,starts)
            value=float(self.weight@mean+penalty*(theta@theta))
            ds=self.weight[self.owner]*mass*(self.edits-mean[self.owner])
            gradient=self.x.T@ds+2*penalty*theta
        return value,gradient

def choose(x,k,columns,beta):
    s=x[:,:,columns]@np.asarray(beta,dtype=float)
    s[np.arange(s.shape[1])[None,:]>=k[:,None]]=-np.inf
    pick=np.argmax(s,axis=1)
    # Use original bank-order argmax. Near ties are recalculated using the
    # same per-bank operation as the original controlled policy.
    ordered=np.sort(s,axis=1)
    near=(k>1)&((abs(ordered[:,-1]-ordered[:,-2])<1e-10)|(abs(ordered[:,-1])<1e-10))
    for i in np.flatnonzero(near):pick[i]=np.argmax(x[i,:k[i]][:,columns]@beta)
    return pick
