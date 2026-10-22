# Manuscript evidence map

| Manuscript content | Public evidence and implementation | Scope |
| --- | --- | --- |
| Table I locked-panel B, N+R and S+R | [Numeric panel inputs](../confirmation_diagnostic/inputs/panel_scores_numeric.jsonl), [aggregate counts](evidence/language_seed_SDIN.csv) | Original locked acquisition policy |
| Direct versus S+R on that panel | [Paired diagnostic and interval](../confirmation_diagnostic/results/confirmation_interval.json), [replay instructions](../confirmation_diagnostic/REPRODUCE.md) | Post-lock retrospective diagnostic |
| Table I TEST and Table II acceptors | [G4/H4/HR4/H3](../experiments/acceptors/), [HWR4/MBR](../experiments/extensions/) | Retrospective TEST; fits use DEV |
| Table III | [Study A](../experiments/cost/study_A_three_checkpoints.json), [Study B](../experiments/cost/study_B_one_checkpoint.json), [profile](../experiments/cost/stage_profile.csv), [runtime](../experiments/runtime/) | Four paths/three checkpoints and seven paths/one checkpoint remain separate |
| RMS scaling sensitivity and checkpoint score diagnostics | [Revision audit](REVISION_AUDIT.md), [CPU fits and numeric evidence](evidence/acceptance_audit/) | Retrospective DEV-selected sensitivity; original fits retained |
| Table IV and non-Persian results | [Language/seed SDIN totals](evidence/language_seed_SDIN.csv), [summary](evidence/COUNT_SUMMARY.json) | Descriptive aggregation of existing counts |
| Empty-candidate and window diagnostics | [Cached controls](../experiments/diagnostics/candidate_controls/), [H4+e](../empty_candidate_diagnostic/) | Retrospective; no new live execution |
| Alternative acquisition gates | [Exact results and replay](evidence/gate_audit/README.md), [independent review](evidence/gate_audit/INDEPENDENT_REVIEW.md) | Fixed cached TEST banks, fixed G4, recording-level routing; no decoding or timing |
| DEV trigger census and empty-output algebra | [Domain/feature audit](evidence/domain_audit/README.md) | Existing DEV and TEST caches; bounded search found no verified unadapted comparator |

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

G4 uses weighted RMS over non-top candidate differences, with normalized
weights proportional to `1 / [N_language * (bank_size - 1)]`. The HF refits use
unweighted pooled RMS over training-fold differences. The implementations are
[the frozen G4 fit](../reproduction/fit/fit_frozen_selector.py) and
[the HF fitting engine](../experiments/acceptors/tools/objective_engine.py).
A CPU sensitivity analysis repeats DEV selection with G4's scaling rule on the
HF banks. Complete CV27 WER changes by +0.044291484116254054 pp (H4),
−0.05658509724889882 pp (HR4) and +0.00286872509053282 pp (HWR4); the order
is unchanged. G4 versus H4 changes both banks and scaling, whereas the HF
acceptor comparisons use common banks, folds and scales.

The outer compression threshold adopts Whisper's standard 2.4 value; the manuscript does not claim
that a DEV search selected it. Selector fitting uses CV27 DEV.

Confirmatory evidence covers the original fixed G4 acquisition comparison.
Later acceptance refits do not inherit confirmation status, and TEST was
accessed during development. Native HF skips N-best rescoring but retains its
internal retry procedure. It is not a single-pass decoder.

Each paired recording block runs on one NVIDIA A40 (48 GB), with blocks
distributed over the four-card server. Memory is per process, not summed across GPUs.

Study B's strategy differences are population-weighted whole-path increments.
The 85.9 ms teacher-scoring and 149.3 ms PLL profile means instead cover all
25 profiled CV27 recordings, including two singletons that skip both stages.
Whole-call allocated-memory maxima do not identify a unique stage or tensor.
Identical triggered algorithmic operations and small trigger-count shares do
not by themselves establish a deterministic wall-clock error bound.

The H3/H4 output partition, H4+e refit and nonempty guard are observed diagnostics.
They do not establish an isolated causal contribution of PLL or guaranteed
short-speech safety. The manuscript preserves these distinctions.

Under G4's observed coefficient signs (+,+,-,-), all positive-token-length
candidates have a negative raw score, whereas zero-feature empties score zero.
Centering or a candidate-independent intercept cannot change this order.
An HF-proposed zero-feature empty therefore wins deterministically when it
enters the selected bank. Only 18 of the complete banks' 19 such CV27 proposals
occur on triggered recordings. The H4+e feature is empty-specific and can change
this ordering; its five DEV empty examples across checkpoints do not establish
general calibration or a verified no-speech termination mechanism.

The alternative word gate reduces calls but loses positive recovery gain.
The token-ID gate retains slightly more gain at additional calls. Both use
recording-level maximum routing and complete-recording word alignments,
including FLEURS's two-window recordings. Neither changes the frozen gate in
Tables I–IV. Tokenization remains language dependent, and new stochastic
decoding under another request schedule need not reproduce the cached draws.

CV27 is a test of cross-domain transfer without CV27 acoustic adaptation;
the selector still uses CV27 DEV. Noise and orthographic mismatch are possible
contributors to the baseline gap, not separately identified causal findings.
