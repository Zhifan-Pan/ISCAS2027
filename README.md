# Selective Recovery for Multilingual ASR: Candidate Acquisition and Acceptance

The current manuscript source and post-lock paired diagnostic are in
[`release_v163/`](release_v163/). Original scientific code and anonymous inputs
remain in [`release_v160/`](release_v160/). Historical releases are unchanged.

## Current snapshot

- [V163 LaTeX source](release_v163/paper_source/), four technical pages plus references.
- Author-supplied final-gi Figure 1, preserved as SVG and PDF vectors across two columns.
- One retrospective Direct-minus-S+R interval, with exact analysis code and anonymous numeric replay inputs.
- Inherited [V162 H4+e fits](release_v162/), all 49-penalty CV records and three final models.
- Separate inherited four-path/three-checkpoint and seven-path/one-checkpoint costs.
- Original same-HF acceptors, HF9/HF12, HWR4/MBR, runtime and numeric inputs in V160.

```sh
python release_v163/verify_release.py
python release_v162/verify_release.py
python release_v160/verify_release.py
```

See [V163 instructions](release_v163/README.md) for what was actually executed
and how to prepare an optional CPU replay. The original confirmation does not
confirm later refits or post-lock diagnostics. H4+e remains retrospective and
does not eliminate the observed empty-output preference. No new GPU timing was
performed for V163. The paired interval is a post-lock descriptive result,
not new confirmation or an equivalence test. Small call rates do not establish
a latency bound, and matching feature architectures do not replace measured costs.

`reproduction/` and `matched_cost_evidence/` retain historical measurements;
their earlier scopes are not the current complete evidence. The historical
README remains [here](docs/historical_readme_v139.md).

Raw audio/reference text, recognizer and LM asset weights, credentials, reviews
and the author's private return bundle are excluded. Obtain original assets
under their providers' terms. Repository availability does not imply conference
submission or acceptance. First-party Python code uses the [MIT license](LICENSE);
see [third-party and data exclusions](THIRD_PARTY_NOTICES.md).
