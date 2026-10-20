# Manuscript-to-evidence map

| Manuscript object | Code or evidence | Scope |
|---|---|---|
| Table I | `paper_source/primary.tex`, `acceptors/counts/`, `acceptors/expected/`, `diagnostics/` | Existing policy branches and accuracy |
| Table II | `acceptors/tools/`, `acceptors/models/`, `acceptors/cv/`, `extensions/` | Same-HF acceptors and extensions |
| Table III A | `cost/study_A_three_checkpoints.json` | Three checkpoints, four policies |
| Table III B | `cost/study_B_one_checkpoint.json` | One checkpoint, seven policies |
| Cost qualifications | `cost/stage_profile.csv`, `cost/trigger_coverage.csv` | Fixed-subset profiles and sample coverage |
| Table IV | `paper_source/language_scope.tex`, `acceptors/expected/per_language_SDIN.csv` | All original languages and denominators |
| HF9/HF12 | `r8/inputs/`, `r8/expected/`, `r8/tools/` | Retrospective gate study |
| H3/H4 partition | `acceptors/branch_audit/` | WER partition, not time or isolated PLL effect |
| Audio policies | `runtime/runtime_v153.py`, `runtime/feature_scoring.py` | Original runtime; new portable CLI wrapper |

`FILE_MANIFEST.json` gives sizes and SHA256 values. `PROVENANCE.json` maps
source and released identities. These are inspection aids, not independent
certification of references or scientific validity.
