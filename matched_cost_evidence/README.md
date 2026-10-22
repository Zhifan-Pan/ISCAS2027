# Earlier paired timing evidence

These records preserve the earlier N+R versus S+R measurement on checkpoint 101
and its output/RNG checks. They are retained as evidence for the original
runtime. The final manuscript's Table III uses the separate
[Study A and Study B summaries](../experiments/cost/), described in the
[manuscript evidence map](../paper/EVIDENCE.md).

## Reading order

| File or directory | Contents |
| --- | --- |
| [TIMING_PROTOCOL.json](TIMING_PROTOCOL.json) and [TIMING_STRATA.json](TIMING_STRATA.json) | Measurement protocol and sampling strata |
| [timing_summary.json](timing_summary.json) | Population-weighted estimates for this earlier two-path study |
| [timing_parity.json](timing_parity.json) and [prediction_parity.json](prediction_parity.json) | Retained timing/output checks |
| [FROZEN_OUTPUT_HASHES.json](FROZEN_OUTPUT_HASHES.json) | Locked output identities |
| [timing/](timing/) | Per-recording measurements and completion records for three rounds |
| [acceleration_v2/](acceleration_v2/) | Recorded scheduling addendum and allocation evidence |
| [private/TIMING_MANIFEST.json](private/TIMING_MANIFEST.json) | Released anonymous sample manifest; the directory name is historical |

The per-recording files support the aggregate estimates and are not obsolete
paper drafts. Their paths and recorded device allocation remain unchanged.
They must not be pooled with the final four-path or seven-path studies.

`reproduce_cost_summary.py` recomputes summaries from these measurements without
launching GPU inference. It writes result files beside its inputs, so run it
only in a separate working copy. For current audio inference entry points, see
the [experiment guide](../experiments/README.md#audio-inference).
