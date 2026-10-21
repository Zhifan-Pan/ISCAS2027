# Selective Recovery for Multilingual ASR: Candidate Acquisition and Acceptance

The current manuscript and matching source are in
[`release_v174/`](release_v174/). Scientific implementations and anonymous replay
inputs remain in [`release_v160/`](release_v160/), with later diagnostics in
[`release_v162/`](release_v162/) and [`release_v163/`](release_v163/).
Historical snapshots are preserved.

## Current manuscript

- [V174 PDF](release_v174/manuscript_v174.pdf): four pages of main content and
  references only on page 5, with 33 references.
- [Complete source](release_v174/paper_source/) and
  [source ZIP](release_v174/source_v174.zip), including the two-column vector figure.
- [Build and verification instructions](release_v174/README.md).
- [Evidence map](release_v174/EVIDENCE.md), including the exact positive-edit
  retention denominator and the four-language results excluding Persian.

The frozen 7,500-recording confirmation panel evaluates acquisition under the
original fixed G4 selector. Post-lock Direct diagnostics, refitted selectors and
development-exposed TEST comparisons are retrospective. Cost Study A measures
four paths across three checkpoints; Study B measures seven paths on one
checkpoint. Their estimates retain their separate scopes.

## Reproduce and verify

Start with the [V160 reproduction guide](release_v160/REPRODUCE.md) for the
scientific code, model fitting records, numeric inputs and audio inference CLI.
The [V162 package](release_v162/) contains H4+e fits, and the
[V163 package](release_v163/) contains the post-lock paired confirmation diagnostic.

```sh
python3 release_v174/verify_release.py
python3 release_v174/verify_aggregates.py
python3 release_v163/verify_release.py
python3 release_v162/verify_release.py
python3 release_v160/verify_release.py
```

The release verifiers check file identity. The aggregate verifier recomputes
summary arithmetic from published numeric summaries. These commands do not
train models, run audio inference, repeat bootstrap inference or measure GPU
latency. No new experiment was needed for this manuscript update.

`reproduction/` and `matched_cost_evidence/` retain historical measurements.
The earlier overview is in [the historical README](docs/historical_readme_v139.md).
Raw audio/reference text, recognizer and LM weights, credentials, reviews and
private author-return bundles are excluded. Repository publication does not
imply conference submission or acceptance. First-party Python code uses the
[MIT license](LICENSE); see [third-party and data exclusions](THIRD_PARTY_NOTICES.md).
