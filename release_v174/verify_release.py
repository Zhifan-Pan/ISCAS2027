#!/usr/bin/env python3
"""Check the V174 snapshot's file and source-archive identity; no experiments."""
import hashlib
import json
from pathlib import Path
import zipfile


def main():
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / "FILE_MANIFEST.json").read_text())
    for name, expected in manifest["files"].items():
        actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
        if actual != expected:
            raise SystemExit(f"Hash mismatch: {name}")
    with zipfile.ZipFile(root / "source_v174.zip") as archive:
        names = {
            "source/" + str(Path(n).relative_to("paper_source"))
            for n in manifest["files"] if n.startswith("paper_source/")
        }
        if set(archive.namelist()) != names:
            raise SystemExit("Source ZIP member set differs from manifest")
        for name in sorted(names):
            local = root / "paper_source" / Path(name).relative_to("source")
            if archive.read(name) != local.read_bytes():
                raise SystemExit(f"Source ZIP differs: {name}")
    print(f"Verified {len(manifest['files'])} files and source ZIP identity.")
    print("Artifact integrity only; not independent scientific validation.")


if __name__ == "__main__":
    main()
