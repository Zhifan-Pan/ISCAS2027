# Reproduce the post-lock confirmation diagnostic

Verify the snapshot from the repository root:

```sh
python confirmation_diagnostic/verify_release.py
```

To prepare a new replay directory, without running an experiment:

```sh
python confirmation_diagnostic/prepare_replay.py --workspace /tmp/confirmation_replay
```

The workspace must not already exist. Optional CPU replay:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 python /tmp/confirmation_replay/confirmation_interval.py \
  --protocol /tmp/confirmation_replay/replay_protocol.json \
  --output-dir /tmp/confirmation_replay/generated
```

The script is byte-identical to the executed analysis code. The preparation
step binds its checksum to order-preserving anonymous numeric inputs. This is
a replay configuration, not a new preregistration. Historical original protocol,
script and result receipts are retained in the metadata. The original analysis
also checked the archived score file identity and confirmation-analysis source
receipt; those historical identities are distinct from the projected inputs.

The projection preserves every policy's SDIN, trigger, language, recording
alignment and sorted speaker-cluster membership. It only removes unused fields
and replaces identifiers. The release preparation verified those invariants,
without executing the bootstrap again. Expected values appear in
`results/confirmation_interval.json`; all 10,000 original bootstrap differences
are in `results/paired_bootstrap.npz`. Timing of this CPU replay has not been
benchmarked; it requires no GPU, model weights, private audio or network.

Metadata such as creation times and absolute replay paths differ between runs;
compare SDIN, estimates and bootstrap draws, not the full JSON byte hash.
