"""Verify snapshot byte identity, not scientific correctness or independence."""
from pathlib import Path
import hashlib
import json

root=Path(__file__).resolve().parent
manifest=json.loads((root/'FILE_MANIFEST.json').read_text())
for row in manifest['files']:
    path=root/row['path']
    assert path.stat().st_size==row['bytes'], row['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'], row['path']
print(f"Verified {len(manifest['files'])} files; no scientific experiment executed.")
