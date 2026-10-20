# Reproduction entry points

From the repository root, verify the release without executing an experiment:

```bash
python release_v160/verify_release.py
python release_v160/runtime/infer_audio.py --help
```

For optional frozen-model numerical replay, use a separate environment and a
fresh output directory:

```bash
python -m pip install -r release_v160/requirements-cpu.txt
cd release_v160
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python acceptors/tools/replay_packaged.py --acceptor-root acceptors --output-dir ../../acceptor_generated
```

This replay recomputes selections, counts and the original bootstrap. It was
not rerun for v160. Do not add `--fit-all` unless intentionally reproducing the
original DEV fits. See [HF gate instructions](r8/README.md) for the separate R8
replay and [audio inference](README.md#audio-inference) for real-audio execution.
Audio and original model assets must be independently obtained.

The new audio CLI wrapper was checked with `--help`; its underlying runtime
is inherited from the completed study. No GPU timing was rerun for publication.
See [environment](ENVIRONMENT.md), [data](DATA.md), [result mapping](RESULTS_MAP.md)
and [limitations](LIMITATIONS.md).
