"""Kernel-held per-pair locks: crash-safe claims, never overwrite accepted pairs."""
import fcntl,json
from pathlib import Path
def claim(root, rows):
    root=Path(root);locks=root/'acceleration_v2/pair_locks';locks.mkdir(parents=True,exist_ok=True)
    for session in range(3):
        for i,row in enumerate(rows):
            dst=root/'timing'/f'session{session}'/(row['anon_id']+'.json')
            if dst.exists():continue
            handle=(locks/f"{session}_{row['anon_id']}.lock").open('a+')
            try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:handle.close();continue
            if dst.exists():handle.close();continue
            dst.parent.mkdir(parents=True,exist_ok=True)
            return session,i,row,dst,handle
    return None
