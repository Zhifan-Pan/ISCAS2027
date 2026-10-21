# Selective Recovery for Multilingual ASR: Candidate Acquisition and Acceptance

The current manuscript and matching source are in
[`release_v166/`](release_v166/). Original scientific code and anonymous
inputs remain in [`release_v160/`](release_v160/). Historical releases
are unchanged.

## Current snapshot

- Final sentence revisions clarify cost-study scope, checkpoint contrasts and the shared scoring pipeline.

- [V166 manuscript PDF](release_v166/manuscript_v166.pdf), four technical pages plus references.
- [Complete V166 source](release_v166/paper_source/) and [source ZIP](release_v166/source_v166.zip).
- Centered table columns and two-row headers, with extended corpus rules in Tables II–IV.
- Revised academic prose and four thematic discussion paragraphs, with unchanged numerical results and method equations.
- Author-supplied symbol-synchronized two-column Figure 1 and all 35 references retained.
- Inherited [V163 post-lock paired diagnostic](release_v163/), including exact analysis code and anonymous replay inputs.
- Inherited [V162 H4+e fits](release_v162/), all 49-penalty CV records and three final models.
- Separate four-path/three-checkpoint and seven-path/one-checkpoint cost studies.
- Original same-HF acceptors, HF9/HF12, HWR4/MBR, runtime and numeric inputs in V160.

```sh
python release_v166/verify_release.py
python release_v163/verify_release.py
python release_v162/verify_release.py
python release_v160/verify_release.py
```

See [V166 instructions](release_v166/README.md) for scope and build details.
No training, inference, GPU timing or bootstrap was performed for V166.
The original confirmation does not confirm later refits or post-lock
diagnostics. H4+e remains retrospective and retains the observed empty-output
acceptances. The paired interval is descriptive, not an equivalence test.
Small call rates do not establish a latency bound; shared scoring architecture
does not replace measured full-policy costs.

`reproduction/` and `matched_cost_evidence/` retain historical measurements;
their earlier scopes are not the current complete evidence. The historical
README remains [here](docs/historical_readme_v139.md).

Raw audio/reference text, recognizer and LM weights, credentials, reviews and
private author return bundles are excluded. Repository availability does not
imply conference submission or acceptance. First-party Python code uses the
[MIT license](LICENSE); see [third-party and data exclusions](THIRD_PARTY_NOTICES.md).
