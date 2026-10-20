"""Original numeric policy reconstruction; no private reference access."""
from common import *
from objective_engine import choose

def reconstruct(p,seed):
    beta=np.asarray(load(A/'acceptors/inputs/G4_LOCK.json')[str(seed)]['raw_beta'])
    bp=choose(p['x'],p['k_beam'],list(range(4)),beta)
    npick=choose(p['x'],p['k'],list(range(4)),beta)
    sp=np.where(p['flags'][p['window_owner']],npick,bp)
    dp=np.where(p['flags'][p['window_owner']],p['hf_index'],bp)
    picks={'RawTop1':np.zeros(len(bp),int),'Native':p['hf_index'],'B':bp,'N':npick,'S':sp,'Direct':dp}
    cs={name:score(p,pk) for name,pk in picks.items()}
    for name in ['B','N','S','Direct']:np.testing.assert_array_equal(cs[name],p[name])
    return cs,picks,beta
