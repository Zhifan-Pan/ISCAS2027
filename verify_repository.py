"""Verify packaged files without running scientific experiments."""
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parent
for package in ("experiments", "empty_candidate_diagnostic", "confirmation_diagnostic", "paper"):
    subprocess.run([sys.executable, str(root/package/"verify_release.py")], check=True)
print("All packages verified.")
