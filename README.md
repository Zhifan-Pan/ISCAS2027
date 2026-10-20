# Selective Recovery for Multilingual ASR: Candidate Acquisition and Acceptance

The current manuscript source and bounded empty-indicator diagnostic are in
[`release_v162/`](release_v162/). Original scientific code and anonymous inputs
remain in [`release_v160/`](release_v160/). Historical releases are unchanged.

## Current snapshot

- [V162 LaTeX source](release_v162/paper_source/), four technical pages plus references.
- Exact H4+e fitting/evaluation code, all 49-penalty CV records and three final models.
- Complete cached-policy checks, language-level SDIN and corrected evidence scopes.
- Separate inherited four-path/three-checkpoint and seven-path/one-checkpoint costs.
- Original same-HF acceptors, HF9/HF12, HWR4/MBR, runtime and numeric inputs in V160.

```sh
python release_v162/verify_release.py
python release_v160/verify_release.py
```

See [V162 instructions](release_v162/README.md) for what was actually executed
and how to prepare an optional CPU replay. The original confirmation does not
confirm later refits or post-lock diagnostics. H4+e remains retrospective and
does not eliminate the observed empty-output preference. No new GPU timing was
performed for V162. Small call rates do not establish a latency bound.

`reproduction/` and `matched_cost_evidence/` retain historical measurements;
their earlier scopes are not the current complete evidence. The historical
README remains [here](docs/historical_readme_v139.md).

Raw audio/reference text, recognizer and LM asset weights, credentials, reviews
and the author's private return bundle are excluded. Obtain original assets
under their providers' terms. Repository availability does not imply conference
submission or acceptance. First-party Python code uses the [MIT license](LICENSE);
see [third-party and data exclusions](THIRD_PARTY_NOTICES.md).
