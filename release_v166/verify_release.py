#!/usr/bin/env python3
"""Verify byte identity of the public V166 snapshot."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parent
manifest = json.loads((root / "FILE_MANIFEST.json").read_text())
for name, expected in manifest["files"].items():
    actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f"Hash mismatch: {name}")
print(f"Verified {len(manifest['files'])} files; integrity only, not scientific validation.")
