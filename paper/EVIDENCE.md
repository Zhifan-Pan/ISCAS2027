# Manuscript evidence map

| Manuscript content | Public evidence and implementation | Scope |
| --- | --- | --- |
| Table I locked-panel B, N+R and S+R | [Numeric panel inputs](../confirmation_diagnostic/inputs/panel_scores_numeric.jsonl), [aggregate counts](evidence/language_seed_SDIN.csv) | Original locked acquisition policy |
| Direct versus S+R on that panel | [Paired diagnostic and interval](../confirmation_diagnostic/results/confirmation_interval.json), [replay instructions](../confirmation_diagnostic/REPRODUCE.md) | Post-lock retrospective diagnostic |
| Table I TEST and Table II acceptors | [G4/H4/HR4/H3](../experiments/acceptors/), [HWR4/MBR](../experiments/extensions/) | Retrospective TEST; fits use DEV |
| Table III | [Study A](../experiments/cost/study_A_three_checkpoints.json), [Study B](../experiments/cost/study_B_one_checkpoint.json), [profile](../experiments/cost/stage_profile.csv), [runtime](../experiments/runtime/) | Four paths/three checkpoints and seven paths/one checkpoint remain separate |
| Table IV and non-Persian results | [Language/seed SDIN totals](evidence/language_seed_SDIN.csv), [summary](evidence/COUNT_SUMMARY.json) | Descriptive aggregation of existing counts |
| Empty-candidate and window diagnostics | [Cached controls](../experiments/diagnostics/candidate_controls/), [H4+e](../empty_candidate_diagnostic/) | Retrospective; no new live execution |

## Rounding and denominators

The locked-panel S+R WER is **32.75476627936039%**, which displays as **32.75%**.
Contrasts use the unrounded values: B minus S+R is 2.2626873830265524 pp,
displayed as **2.26 pp**. Rounding an intermediate 32.755 value would give a
different display and is not the calculation used in the paper.

For each language and seed, let G be positive word-edit gain available from
N+R relative to B, L the corresponding lost gain under S+R, and N the full
language reference-word count. The retention estimand is
`100 * (1 - mean(L/N) / mean(G/N))`, with equal language and seed weights.
The [30 denominator cells](evidence/retention_denominators.csv) give
**99.98258136777363%** on CV27, displayed as **99.98%**. The pooled edit ratio is
99.98001039459481%, a distinct estimand. The **370 of 373** statistic counts
beneficial seed-recording instances, not unique recordings or word edits.

Excluding Persian, the four-language macro WER reduction is
**0.6098827948703445 pp** on CV27 TEST and **0.4505660669817182 pp** on the locked
confirmation panel, displayed as **0.61 pp** and **0.45 pp**. These are descriptive
aggregates, not additional subgroup significance tests.

## Interpretation retained in the manuscript

Confirmatory evidence covers the original fixed G4 acquisition comparison.
Later acceptance refits do not inherit confirmation status, and TEST was
accessed during development. Native HF skips N-best rescoring but retains its
internal retry procedure. It is not a single-pass decoder.

Study B's strategy differences are population-weighted whole-path increments.
The 85.9 ms teacher-scoring and 149.3 ms PLL profile means instead cover all
25 profiled CV27 recordings, including two singletons that skip both stages.
Whole-call allocated-memory maxima do not identify a unique stage or tensor.
Identical triggered algorithmic operations and small trigger-count shares do
not by themselves establish a deterministic wall-clock error bound.

The H3/H4 output partition, H4+e refit and nonempty guard are observed diagnostics.
They do not establish an isolated causal contribution of PLL or guaranteed
short-speech safety. The manuscript preserves these distinctions.
