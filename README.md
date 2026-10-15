# Selective Recovery for Multilingual ASR: Candidate Acquisition and Acceptance

Reproduction code and anonymized numerical evidence for the submitted manuscript. The package reproduces the complete five-language evaluation and the paired N+R/S+R cost estimates reported in the paper.

Reported accuracy: 17.087% and 31.681% macro WER on the complete five-language FLEURS and Common Voice v27 TEST splits over three checkpoints, matching the unconditional-recovery control to within 0.001 pp, preserving 370 of 373 beneficial Common Voice recoveries, at a 0.09-0.30% invocation rate pooled over recordings. Paired stratified measurements estimate 5.09% and 4.40% lower mean latency at one checkpoint.

The package contains no audio, model weights, raw reference transcripts or client names. The numerical inputs use anonymous recording IDs. Model and corpus access remains subject to the original providers' terms.

## Verified CPU commands

Run these commands from this package directory with Python 3.10+ and the versions in `reproduction/requirements-cpu.txt`:

```bash
python reproduction/cache/replay_core.py
python reproduction/cache/replay_completed_native.py
python reproduction/cache/replay_v119.py
python reproduction/fit/fit_frozen_selector.py
python matched_cost_evidence/reproduce_cost_summary.py
```

- `replay_core.py`: complete saved source-control WER, 108 learned-gate points, held-out DEV source decisions and component deletion checks.
- `replay_completed_native.py`: all three Native checkpoints, N+R results and the paired CV27 conditional interval.
- `replay_v119.py`: useful-recovery retention and the one fixed, retrospective score intervention. It does not select a new method.
- `fit_frozen_selector.py`: fits all three final DEV selectors at their previously selected penalties and checks the exported coefficients. The original cross-validation search is documented but is not rerun by this command.
- `reproduce_cost_summary.py`: reconstructs the two-path means, paired stratified intervals and observed memory peaks from 2,181 anonymous accepted pairs. It does not perform new timing.

All five commands passed after copying the package to an isolated temporary directory and removing site-specific Python path/asset environment settings. This used the existing pinned environment, not a fresh dependency installation. See `REPRODUCTION_VALIDATION.json`.

## Raw-audio entry and remaining boundary

`reproduction/raw/infer_audio.py` and `runtime.py` contain the matched N+R/S+R implementation. The portable helper modules, generation configurations, model identities, selector coefficients and asset hashes are included. The CLI has been checked; a new isolated, branch-covering GPU run of this packaged entry has **not** been completed. Cached CPU reproduction is not raw-audio reproduction.

After obtaining the matching assets legally, copy `reproduction/config/ASR_REPRO_CONFIG.example.json`, replace its paths and create an audio manifest. Each JSON-list entry needs `path`, `lang`, `uid`, `split` and optionally `anon_id`. Preserve the original `uid` and `split` for the same random mapping; omitting references from the inference manifest is recommended. On this shared server obtain the current genuine GPU admission before loading models. This package does not grant GPU access.

```bash
python reproduction/raw/infer_audio.py \
  --portable-root reproduction/portable \
  --assets-config /path/to/ASR_REPRO_CONFIG.json \
  --manifest /path/to/audio_manifest.json \
  --selector-lock reproduction/raw/SELECTOR_LOCK.json \
  --seed 101 --policy SplusR --output /path/to/new_predictions.jsonl
```

The raw entry reproduces outputs. Formal timing additionally needs same-card interleaved pairs, synchronization, warmup and interference rejection under the frozen timing protocol. Its output should not be presented as the published paired benchmark.

## Evidence scope

Accuracy covers complete five-language official TEST: 3,665 FLEURS and 58,514 CV27 recordings, each at three checkpoints. These are retrospective evaluations. The useful-recovery counts are checkpoint–recording instances: 10/373, corresponding to 9/278 distinct recordings. The CV27 useful set spans 249 client/reference components.

Timing covers checkpoint 101 only: 255/472 stratified sampled recordings, three rounds, 2,181 same-card pairs. It is population-weighted estimation, not complete-population timing. The accepted historical measurements used three A40 devices (physical 0/2/3); the archive records their actual allocation. Current GPU policy is separate and must be followed for any new run. Models are resident; initialization/warmup is excluded. This comparison is N+R versus S+R, not Native-alone versus S+R or no-acquisition-alone versus S+R. Peak memory is not reduced.

**Scope.** The five-language evaluation and the Czech/Slovak results are retrospective. Bulgarian and Croatian predictions were locked before reference access, but on those two corpora the trigger does not separate acquisition from no acquisition, so they bound the method's applicability rather than confirm it.
