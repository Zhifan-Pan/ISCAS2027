# V162 precision revision and bounded empty-indicator diagnostic

The [paper source](paper_source/BUILD.md) builds to four technical pages plus
one references-only page. It retains the original figure, author information,
35 references, component checkmarks and core results. It adds precise n-gram/RMS
definitions, the repaired math-hat text mapping, within-study cost contrasts,
and an evidence-grounded explanation of rounded FLEURS gains and empty outputs.

## What was executed

H4+e adds an exactly-raw-empty indicator and refits all coefficients using the
original component folds, 49 penalties, training-fold RMS and risk objective.
All 735 CV and three final CPU fits converged. CV27 complete-policy WER is
31.52351688586994%; all 18 empty acceptances remain. This is a retrospective
diagnostic, not a replacement for G4 or a newly confirmed strategy.

`cv/`, `models/` and `protocols/` retain all fitted records. `results/` contains
new cached-policy checks, full-language SDIN, selected candidate indices and
complete-recording error counts. Original inputs remain byte-identical in
[`release_v160/`](../release_v160/README.md), including numeric-only empty masks
and normalized-text digests. No new GPU timing or confirmation was performed.

The fitting/evaluation scripts are the exact executed versions, including all
assertions. A preparation script recreates their original relative layout using
only previously released anonymous numeric inputs; it starts no experiment.

```sh
python release_v162/verify_release.py
python release_v162/prepare_replay.py --workspace /path/to/new/replay
# Optional frozen-model evaluation, on CPU, once the workspace is prepared:
python /path/to/new/replay/revision_v162/tools/check_evidence.py candidates
python /path/to/new/replay/revision_v162/tools/check_evidence.py refit
```

Use NumPy/SciPy from the recorded environment in each CV RESULT.json. To
independently refit, use a separate prepared workspace and run
`fit_empty_acceptor.py --root /path/to/new/replay/revision_v162 --data-root
/path/to/new/replay/final_decision_return/reviewer_artifact/acceptors/inputs
--seed 101 --family H4plusE` for each of the three recorded seeds. Refitting
is optional reproduction, not required to read or verify the released results.
Existing CV directories are protected from overwrite. The original protocol's
time records remain historical, not a new preregistration for a replay.

The `costs` phase of check_evidence.py records the author's original profile
file receipts and requires that original directory layout. Its strategy
contrasts are already provided in results/cost_audit and are simple subtractions
of the inherited study-B weighted means. The 25-recording CV27 profile is
unweighted, includes two records skipping scoring, and is not an active-only
subset. A policy difference is not an isolated stage duration.

## Evidence boundaries

- Five original FLEURS gains round to 0.37 pp; H3 differs by two edits on one
  trigger. This is not exact equality of all selectors' gains or output texts.
- Empty TEST candidates come from HF outputs; the termination/no-speech branch
  was not logged. Empty guarding and B reversion match on these actual caches.
- Five FLEURS and 207 CV27 later-checkpoint triggers are absent from the timing
  sample. Their millisecond impact is unknown. Cost A and B retain distinct scopes.
- The confirmation panel lacks full candidate features for H4/HWR4. Its original
  identity covers only frozen original policies; Direct/Native are post-lock.
- Complete H4/H3/HWR4/H4+e and trigger-selective PLL costs remain unmeasured.

Private transcripts/audio, original recording identifiers, model asset weights,
credentials, task/review documents and the author return are excluded. This
publication is not a conference submission or an acceptance claim.
