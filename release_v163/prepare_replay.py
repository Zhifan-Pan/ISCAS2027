"""Prepare an anonymous-input CPU replay without executing it."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--workspace',type=Path,required=True)
    args=ap.parse_args();root=Path(__file__).resolve().parent
    manifest=json.loads((root/'FILE_MANIFEST.json').read_text())
    for item in manifest['files']:
        p=(root/item['path']).resolve()
        assert p.is_relative_to(root)
        assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256']
    out=args.workspace.resolve();out.mkdir(parents=True,exist_ok=False)
    shutil.copytree(root/'inputs',out/'inputs')
    shutil.copy2(root/'tools/confirmation_interval.py',out/'confirmation_interval.py')
    lock=json.loads((root/'protocols/REPLAY_TEMPLATE.json').read_text())
    for item in lock['inputs']:item['path']=str(out/item['path'])
    lock['scores']=str(out/lock['scores']);lock['count_dir']=str(out/lock['count_dir'])
    (out/'replay_protocol.json').write_text(json.dumps(lock,indent=2)+'\n')
    print(f'Prepared {out}; no scientific computation executed.')


if __name__=='__main__':main()
