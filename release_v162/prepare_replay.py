"""Prepare a NEW replay workspace from released bytes, without running science."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--workspace', type=Path, required=True)
    a = p.parse_args()
    release = Path(__file__).resolve().parent
    inherited = release.parent / 'release_v160'
    work = a.workspace.resolve()
    work.mkdir(parents=True, exist_ok=False)
    current = work / 'revision_v162'
    current.mkdir()
    for name in ['tools', 'models', 'protocols']:
        shutil.copytree(release / name, current / name)
    (current / 'analysis').mkdir()
    (current / 'cv').mkdir()
    mappings = {
        'final_decision_return/reviewer_artifact/acceptors': inherited / 'acceptors',
        'revision_v152/private': inherited / 'extensions/numeric_inputs',
        'revision_v152/models': inherited / 'extensions/models',
    }
    for name, target in mappings.items():
        assert target.exists(), target
        dst = work / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.symlink_to(target, target_is_directory=True)
    shutil.copytree(release / 'input_receipts', work / 'revision_v152/analysis/input_export')
    plan = json.loads((current / 'protocols/H4plusE_LOCK.json').read_text())
    sha = lambda q: hashlib.sha256(q.read_bytes()).hexdigest()
    for seed in plan['seeds']:
        assert sha(inherited / f'acceptors/inputs/DEV_{seed}.npz') == plan['DEV_input_sha256'][str(seed)]
        assert sha(inherited / f'extensions/numeric_inputs/DEV_{seed}_diagnostics.npz') == plan['DEV_diagnostics_sha256'][str(seed)]
    for name, expected in plan['code_sha256'].items():
        assert sha(current / 'tools' / name) == expected
    print(f'Prepared {current}; no fitting, evaluation, timing or bootstrap executed.')

if __name__ == '__main__':
    main()
