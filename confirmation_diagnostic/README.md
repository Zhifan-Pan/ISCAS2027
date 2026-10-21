# Post-lock confirmation diagnostic

This diagnostic reports a retrospective paired interval from existing
confirmation-panel counts. Direct minus S+R is −0.05 pp, with a descriptive
95% interval [−0.19, +0.04]. It does not inherit the original confirmation status.
No new model, inference, confirmation collection or GPU timing was run.

```sh
python confirmation_diagnostic/verify_release.py
```

This command verifies shipped files without rerunning the experiment. See
[REPRODUCE.md](REPRODUCE.md) for an optional CPU replay. Minimal numeric inputs
retain SDIN counts and ordered speaker-cluster membership, with anonymous IDs.
They contain no audio, reference transcripts or original recording/speaker IDs.

The H4+e fits and diagnostics remain in [Empty-candidate refits](../empty_candidate_diagnostic/README.md).
Original acceptors, controls and timing inputs remain in
[Scientific implementation](../experiments/README.md). Scientific result files retain their original bytes.

| Evidence | Interpretation |
|---|---|
| N+R and S+R match on each frozen-panel seed | Evidence for the original acquisition control |
| HR4 trails H4 on all three observed seeds | This matched-bank, unweighted RankNet instance |
| Direct and HWR4 mean advantages | Concentrated in particular checkpoints and dependent on source |
| Nonempty guard retains 91.52% of CV27 gain | Cached sensitivity; excludes empty outputs, not all deletions |
| Cost A and B | Distinct measured studies, not interchangeable timing samples |

See [LIMITATIONS.md](LIMITATIONS.md) for the sampling, confirmation and cost
boundaries. Repository publication is not conference submission or acceptance.
No author-return documents, review reports, task instructions or credentials are
included. The repository license and third-party notices continue to apply.
