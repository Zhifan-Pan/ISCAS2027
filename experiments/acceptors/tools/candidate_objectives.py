#!/usr/bin/env python3
"""Reference objectives for the PROPOSED matched-HF acceptor study.
Not a rerun of the paper's historical training, and not a complete training pipeline.
DEV must be single-window; TEST multi-window scoring requires full-recording text.
No script in this module accesses audio, model APIs, TEST labels or confirmation data.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

@dataclass
class Banks:
    features: np.ndarray  # (total candidates, feature dimensions), training-scaled differences
    offsets: np.ndarray  # length n_banks+1, all banks nonempty
    edits: np.ndarray    # candidate word edits, DEV single-window recording references
    words: np.ndarray    # per-bank reference words
    languages: np.ndarray

    def validate(self):
        x=np.asarray(self.features); o=np.asarray(self.offsets); e=np.asarray(self.edits)
        w=np.asarray(self.words); l=np.asarray(self.languages)
        if x.ndim!=2 or len(x)==0 or not np.isfinite(x).all():raise ValueError('Finite candidate feature matrix required')
        if o.ndim!=1 or o.dtype.kind not in 'iu' or len(o)<2 or o[0]!=0 or o[-1]!=len(x) or not (np.diff(o)>0).all():raise ValueError('Invalid offsets')
        if e.shape!=(len(x),) or e.dtype.kind not in 'iu' or (e<0).any():raise ValueError('Nonnegative integer candidate edits required')
        if w.shape!=(len(o)-1,) or w.dtype.kind not in 'iu' or (w<0).any():raise ValueError('Invalid reference words')
        if l.shape!=w.shape or l.dtype.kind not in 'iu':raise ValueError('Invalid language labels')
        for j in np.unique(l):
            if w[l==j].sum()<=0:raise ValueError('Zero language reference denominator')
        return self

    def weights(self):
        self.validate();l=np.asarray(self.languages);w=np.asarray(self.words)
        langs=np.unique(l); out=np.empty(len(w),dtype=float)
        for j in langs:out[l==j]=1./(len(langs)*float(w[l==j].sum()))
        return out


def relative_features_and_rms(features, offsets, train_banks):
    """Training-only pooled RMS of non-top differences; same scales for test export.
    Calling code MUST restrict offsets/data before any held-out model fit.
    """
    x=np.asarray(features,dtype=float);o=np.asarray(offsets)
    if x.ndim!=2 or o.ndim!=1 or o[0]!=0 or o[-1]!=len(x) or not (np.diff(o)>0).all():raise ValueError('Invalid feature bank')
    train=np.asarray(train_banks)
    if train.shape!=(len(o)-1,) or train.dtype!=np.dtype(bool) or not train.any():raise ValueError('Training-bank mask required')
    rel=x.copy();samples=[]
    for i,(a,b) in enumerate(zip(o[:-1],o[1:])):
        rel[a:b]-=x[a]
        if train[i] and b-a>1:samples.append(rel[a+1:b])
    scale=np.sqrt(np.mean(np.concatenate(samples)**2,axis=0)) if samples else np.ones(x.shape[1])
    scale=np.where(scale<1e-12,1.,scale)
    if not np.isfinite(scale).all():raise ValueError('Nonfinite scale')
    return rel/scale,scale


def risk_value_grad(theta, banks: Banks, penalty: float):
    banks.validate(); theta=np.asarray(theta,dtype=float)
    if theta.shape!=(banks.features.shape[1],) or not np.isfinite(theta).all() or not np.isfinite(penalty) or penalty<0:raise ValueError('Invalid parameters')
    x=banks.features;o=banks.offsets;e=banks.edits.astype(float);weights=banks.weights()
    lengths=np.diff(o); owner=np.repeat(np.arange(len(lengths)),lengths)
    score=x@theta; maxima=np.maximum.reduceat(score,o[:-1]); mass=np.exp(score-maxima[owner]); mass/=np.add.reduceat(mass,o[:-1])[owner]
    mean=np.add.reduceat(mass*e,o[:-1]); value=float(weights@mean+penalty*(theta@theta))
    dscore=weights[owner]*mass*(e-mean[owner]);gradient=x.T@dscore+2*penalty*theta
    return value,gradient


def rank_pairs(banks: Banks):
    """Unordered unequal-edit pairs; better-minus-worse feature differences.
    Each bank's total pair weight = 1/(L*N_language); ties produce no pairs.
    """
    banks.validate();weights=banks.weights();d=[];w=[]
    for i,(a,b) in enumerate(zip(banks.offsets[:-1],banks.offsets[1:])):
        pairs=[]
        for j in range(a,b):
            for k in range(j+1,b):
                if banks.edits[j]==banks.edits[k]:continue
                good,bad=(j,k) if banks.edits[j]<banks.edits[k] else (k,j)
                pairs.append(banks.features[good]-banks.features[bad])
        if pairs:
            d.extend(pairs);w.extend([weights[i]/len(pairs)]*len(pairs))
    return np.asarray(d,dtype=float).reshape(-1,banks.features.shape[1]),np.asarray(w,dtype=float)


def rank_value_grad(theta, differences, pair_weights, penalty: float):
    t=np.asarray(theta,float);d=np.asarray(differences,float);w=np.asarray(pair_weights,float)
    if d.ndim!=2 or t.shape!=(d.shape[1],) or w.shape!=(len(d),) or not np.isfinite(d).all() or not np.isfinite(w).all() or (w<0).any() or not np.isfinite(t).all() or not np.isfinite(penalty) or penalty<0:raise ValueError('Invalid pair problem')
    margin=d@t; value=float(w@np.logaddexp(0.,-margin)+penalty*(t@t))
    # 1/(1+exp(margin)), computed without overflow.
    neg_sigmoid=np.exp(-np.logaddexp(0.,margin)); gradient=-(d.T@(w*neg_sigmoid))+2*penalty*t
    return value,gradient


def hard_macro_wer(theta,banks: Banks):
    banks.validate();s=banks.features@np.asarray(theta);errors=[]
    for a,b in zip(banks.offsets[:-1],banks.offsets[1:]):
        errors.append(banks.edits[a+int(np.argmax(s[a:b]))])  # original bank order tie rule
    return float(100*banks.weights()@np.asarray(errors))
