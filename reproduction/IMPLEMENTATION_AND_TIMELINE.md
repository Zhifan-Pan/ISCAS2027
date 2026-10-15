# Definitions and provenance boundary

## Selectors, folds and normalization

`config/SELECTORS.json` gives the actual RMS scales, penalties, scaled coefficients and raw coefficients for both beam-bank and expanded-bank fits at every checkpoint. Each checkpoint is fitted independently. Sharing means across languages, sources and invocation policies within a checkpoint; it does not mean one numerical coefficient vector for all three ASR checkpoints.

`fit/data/DEV_{101,202,303}.npz` contains the 58,171 complete CV27 DEV feature/count rows per checkpoint, anonymous IDs, five folds and opaque connected-component indices. Only the four used feature columns are exported. No reference text or speaker name is included. Group membership does not cross folds. `config/FIT_CONFIG.json` records all 49 penalties, optimizer settings and source hashes. Model choice minimizes pooled held-out hard macro WER, then prefers the larger penalty on a tie; final models refit complete DEV. The CPU command validates final fitting at the frozen penalties, not a fresh cross-validation selection.

Raw feature order is body-token mean decoder log probability, original-string tokenwise XLM-R PLL, log(1 + body-token count), and normalized-word repeated-four-gram proportion with threshold three. Prefix, EOS and padding are excluded from body-token scores. Empty raw features equal zero before subtracting top-beam features. The four feature differences are RMS-scaled on valid non-top candidates with weights proportional to 1 / [language reference words × (bank size − 1)]. Singleton rows do not define scales. L-BFGS-B starts at zero. Hard selection uses original bank-order ties.

`portable/vendor/wer_rules_v3.py` is the exact normalization used for WER, repetition and deduplication. First-occurrence deduplication precedes appending one final recovery hypothesis; an existing normalized candidate is not replaced. The expanded bank has at most six entries and is not truncated again. Intermediate fallback outputs are excluded.

The learned benefit gate uses **negative** predicted edit reduction as its score, then invokes when the score is below the DEV quantile. Nine features: log(1 + duration), log(1 + beam-bank size), decoder gap, entropy, decoder-score standard deviation and range, length range, repetition range, and mean absolute top-relative decoder difference. The 12-feature version adds raw top-beam compression, absolute top-beam repetition and maximum beam repetition. Frozen models/thresholds are in `cache/data/FINAL_DEV_LOCK_*.json`.

## Generation and random mapping

`portable/bindings/evidence/GENERATION_FREEZE.json` and the effective-generation file record native suppression and first-search configuration. The raw entry uses Transformers 4.57.6, beam width five, max 444 new tokens, known language, no previous-window text, bfloat16. It splits complete audio into nearly equal windows of at most 480,000 samples at 16 kHz. Both paths reuse only their own encoder and initial search. All source hypotheses in N+R and S+R use the same random mapping.

The outer trigger computes raw UTF-8 byte length divided by zlib compressed length, exceeding 2.4; any triggering window expands all windows. The inner HF fallback separately uses temperatures 0, .2, .4, .6, .8, 1 and token-byte compression/log probability/no-speech thresholds 1.35 / −1 / .6. These are different quantities and gates.

The isolated sampled-source control seeds each window from the first eight hex digits of SHA256(`V146|source|checkpoint|split|language|uid|window`). Native fallback instead uses SHA256(`V114|split|language|uid`) to seed a recording and carries its RNG state across its windows. This HF mapping intentionally does not contain checkpoint or window. The paper now distinguishes the two mappings. No predictions were regenerated to make this wording correction.

## Cost exclusions

The historical benchmark accepted 2,181 pairs and logged 23 pair rejections due to external GPU activity. NVML sampled compute PIDs every 100 ms plus pair-boundary/epoch checks. A disturbed pair is rejected as a whole, without examining its latency. The 23 count is not an exhaustive count of process kills or failures that happened before a record was logged. It must not be called an all-attempt rejection rate.

Work counters show actual generation-call reductions with unchanged encoder counts. They are not a stage-time decomposition: the historical benchmark did not record independent stage milliseconds. No matched Native-alone or no-acquisition-alone latency is included; old differently measured timing cannot fill those cells.

## What can be reconstructed about the timeline

These are verifiable artifact milestones, not fabricated dates of first label access:

- The Oct. 3 control protocol explicitly describes TEST-informed development. Five-language TEST therefore remains retrospective in every later manuscript.
- Oct. 14 matched source and complete Native/N+R artifacts contain locked coefficients/predictions and full TEST scoring. A prediction lock before one scoring script does not erase earlier TEST exposure.
- Oct. 15 matched timing reached 2,181 verified pairs; the dynamic-allocation addendum and actual device map preserve how they were run.
- V119 reuses those predictions, computes helpful-recovery accounting, checks actual-winner score margins and applies one explicitly retrospective margin intervention. It does not retune or replace the primary method.

The first access time for every historical dataset/label is not established by file modification timestamps. Previously used CV27 TRAIN-derived calibration pools are not untouched confirmation data. No new positive independent confirmation, full split-overlap audit, public release or clean-environment raw-audio reproduction is claimed by this package.
