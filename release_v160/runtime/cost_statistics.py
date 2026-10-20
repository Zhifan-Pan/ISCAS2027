"""Paired, stratum-weighted fixed-session statistics, independent of runtime."""
import numpy as np


def stratified_summary(groups, population, draws=4000, seed=15301):
    """groups: (population_count, [sample_recording,policy] round means)."""
    assert sum(M for M,a in groups)==population
    policies=groups[0][1].shape[1]
    mean=np.zeros(policies,dtype=float)
    boot=np.zeros((draws,policies),dtype=float)
    rng=np.random.default_rng(seed)
    for M,a in groups:
        a=np.asarray(a,dtype=float);n=len(a)
        assert a.ndim==2 and a.shape[1]==policies and 0<n<=M
        assert np.isfinite(a).all() and (a>0).all()
        base=a.mean(0);weight=M/population
        mean+=weight*base
        boot+=weight*base
        if n<M:
            fpc=np.sqrt((M-n)/(M-1))
            # Every sampled index applies to every policy, preserving pairing.
            for b in range(draws):
                boot[b]+=weight*fpc*(a[rng.integers(n,size=n)].mean(0)-base)
    return mean,boot
