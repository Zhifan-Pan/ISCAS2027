"""Verify shipped bytes without fitting, inference, bootstrapping or network IO."""
from pathlib import Path
import hashlib
import json


def main():
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / 'FILE_MANIFEST.json').read_text())
    for item in manifest['files']:
        path = root / item['path']
        assert path.is_relative_to(root) and path.is_file(), item['path']
        assert path.stat().st_size == item['bytes'], item['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'], item['path']
    print(f"Verified {len(manifest['files'])} released files; no scientific experiment executed.")


if __name__ == '__main__':
    main()
