# Numeric data boundary

`inputs/panel_scores_numeric.jsonl` contains only seed, language, anonymous
recording ID, anonymous within-language speaker cluster, trigger and B/Native/
N+R/S+R substitution, deletion, insertion and reference-word counts.
The three `counts_*.npz` files add the already reconstructed post-lock Direct
counts. Their IDs are `CF00000` through `CF07499`.

There are 7,500 distinct CV27 recordings and three checkpoint observations per
recording. Language order in NPZ is ar, fa, pl, tr, it. Score sorting and speaker
cluster ordering are preserved by anonymous, ordered labels. No mapping to raw
identifiers is shipped. Recordings across checkpoints are paired observations,
not independent extra recordings.

The original audio and reference text remain under Common Voice terms and are
not included. No acoustic silence labels, stage-termination labels or complete
confirmation candidate-feature banks are provided. The numeric projection
supports only the reported count-based paired diagnostic, not new inference or
refitting on the confirmation panel.
