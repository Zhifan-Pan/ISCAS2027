# Current manuscript code snapshot

This snapshot accompanies manuscript v160, a presentation update to v159.
The only paper changes are checkmark component columns in Tables I/II and
the GitHub link at the end of the abstract. Scientific inputs, models and
reported measurements are inherited unchanged. No experiment was rerun to
publish this snapshot.

## Contents

- `acceptors/`: anonymous full DEV/TEST candidate features, complete-recording
  single/two-window error tables, G4 and nine H4/HR4/H3 models, all 49-penalty
  CV records, counts, implementation and original replay program.
- `r8/`: frozen HF9/HF12 inputs, coefficients/thresholds and original replay.
- `extensions/`: HWR4 models, CV, numeric-only candidate-distance inputs,
  MBR/HWR4 evaluation code and inherited results. Local author paths were
  adapted for this package; objectives, arrays and assertions were retained.
- `runtime/`: the exact seven-policy inference and scoring implementation used
  in the completed output/RNG and cost study, with a parameterized audio CLI.
- `cost/`: separate three-checkpoint/four-path and one-checkpoint/seven-path
  measured summaries; existing unweighted subset profiles and coverage audit.
- `diagnostics/`: inherited V159 post-lock Direct, guard and window diagnostics.
- `paper_source/`: independently compilable manuscript source and original figure.

## Verify without starting experiments

Detailed guides: [reproduction](REPRODUCE.md), [environment](ENVIRONMENT.md),
[data](DATA.md), [experiments](EXPERIMENTS.md), [result mapping](RESULTS_MAP.md)
and [limitations](LIMITATIONS.md).

From the repository root:

```bash
python release_v160/verify_release.py
python release_v160/runtime/infer_audio.py --help
```

Install `release_v160/requirements-cpu.txt` in an isolated environment for
numerical replay. The original acceptor replay is documented in
`acceptors/README.md`; it defaults to frozen-model evaluation. `--fit-all`
would repeat training and is an optional reproduction operation, not a step
performed for this publication. For HWR4/MBR replay, copy `extensions/` to a
fresh output workspace alongside `acceptors/` first; existing output folders
are intentionally protected from overwrite. Fit code is supplied to inspect
or independently reproduce the original DEV procedure, not to retune on TEST.

The original R8 replay has a known environment-sensitive intermediate
`1e-12` assertion in Python 3.13/NumPy 2.3.5. It was retained unchanged;
no checks were removed or relaxed to manufacture a successful replay.
Use the documented author environment and distinguish inherited execution
records from any new execution.

## Audio inference

Obtain corpus audio, Whisper/LoRA and XLM-R assets under their providers' terms.
Use the repository's existing `reproduction/portable` helpers and example asset
configuration. The CLI accepts all seven policies and the original seed/UID
mapping. It executes real audio inference and never substitutes cached outputs.
Use `--residency matched` to load both models as in the cost study. `Native`,
`RawTop1` and `H3Direct` execute no PLL; `--residency policy` also avoids
loading XLM-R for those paths. That deployment configuration has no published
latency or memory measurement. Follow your own site's GPU admission rules.

```bash
python release_v160/runtime/infer_audio.py \
  --portable-root reproduction/portable \
  --assets-config /path/to/ASR_REPRO_CONFIG.json \
  --manifest /path/to/audio_manifest.json \
  --seed 101 --policy H3Direct --residency matched \
  --output /path/to/new_predictions.jsonl
```

## Scope

The original 7,500-recording panel confirms only the original frozen policy.
Direct panel numbers are post-lock retrospective diagnostics; HWR4 lacks
candidate-level inputs on that panel. Later gates and acceptors do not inherit
confirmation. TEST informed development. Cost A and B use different checkpoint
scopes and must not be pooled; a first-checkpoint census misses some later
checkpoint triggers. Stage means are unweighted fixed-subset descriptions,
not population time shares. Complete H4/H3 and new selective-PLL costs remain
unmeasured. The fixed nonempty guard worsened CV27 WER.

No audio, reference transcript, recognizer/LM weights, original client names,
credentials, reviewer reports or author-internal return bundle is distributed.
Anonymous counts/features and model fitting coefficients are provided for
reproduction. Source hashes in `PROVENANCE.json` establish file identity,
not reference independence or scientific validity. Directory labels named
`expected` retain their role as inherited comparison outputs.
