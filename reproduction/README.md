# Original acquisition implementation and evidence

This directory preserves the original acquisition fits, numeric inputs and
portable inference dependencies. For the final manuscript and its evidence map,
start with [paper/](../paper/README.md). For HF acceptor controls and the final
Table III studies, use [experiments/](../experiments/README.md).

## File guide

| Path | Purpose |
| --- | --- |
| [config/](config/) | Locked selector coefficients, RMS scales and fit settings |
| [fit/](fit/) | DEV-only final-fit replay at the locked penalties and numeric inputs |
| [cache/](cache/) | Original cached inputs, prediction counts and replay programs |
| [analyses/](analyses/) | Acquisition-gain and winner diagnostics |
| [portable/](portable/) | Inference dependencies, generation settings and asset configuration |
| [raw/](raw/) | Raw-audio inference entry points; audio and model assets are not included |
| [historical_math/](historical_math/) | Archived objective implementations retained for comparison |

[Definitions and provenance](IMPLEMENTATION_AND_TIMELINE.md) describe feature
normalization, candidate ordering, random mappings and the scope of the earlier
timing records. [Baseline grids](BASELINE_GRIDS.md) document the retained controls.

The original G4 fit uses weighted RMS over valid non-top candidate differences,
with normalized weights proportional to
`1 / [language reference words * (bank size - 1)]`. The later HF acceptor refits
use unweighted pooled RMS over their training-fold differences, as implemented
in [objective_engine.py](../experiments/acceptors/tools/objective_engine.py).

## Reproduction scope

Follow the [reproduction entry points](../experiments/REPRODUCE.md) for the final
controls. Run any replay that writes results from a separate working copy, so
published inputs, fitted coefficients and expected outputs remain unchanged.
The final-fit replay here validates the frozen penalties; it does not repeat
the cross-validation search. Historical identifiers inside files are retained
for traceability and are not alternate manuscript versions.
