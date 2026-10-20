# Selective Recovery for Multilingual ASR: Candidate Acquisition and Acceptance

The current V161 manuscript source is in [`release_v161/`](release_v161/).
Scientific code and anonymous numerical exports remain in
[`release_v160/`](release_v160/). The paper separates candidate acquisition
from acceptance and reports the original frozen-panel evaluation alongside
retrospective source/acceptor comparisons.

## Current snapshot

- Layout-corrected [V161 LaTeX source](release_v161/paper_source/), retaining the checkmark component ablations.
- Complete same-HF candidate-acceptor code, frozen models and 49-penalty logs.
- HF9/HF12, HWR4 and MBR code, original numerical inputs and inherited results.
- Real-audio seven-policy runtime, including RawTop1 and H3Direct.
- Distinct cost evidence for four paths across three checkpoints and seven
  paths at one checkpoint; measured uncertainty and remaining limitations.

```bash
python release_v161/verify_release.py
python release_v160/verify_release.py
```

See [instructions and evidence scope](release_v160/README.md) before replaying
or measuring. No new experiment was performed for this code publication.
The original confirmation does not confirm later refits or post-lock diagnostics.

## Historical material

`reproduction/` and `matched_cost_evidence/` preserve earlier code/evidence.
Their earlier two-path or one-checkpoint results are historical; use the
current snapshot for present manuscript scopes. The previous README is
preserved in [docs/historical_readme_v139.md](docs/historical_readme_v139.md).

Raw audio, reference transcripts, base/adapter weights, credentials, reviews
and the author's private return bundle are excluded. Obtain original assets
under their providers' terms. Repository availability is not a claim of
conference submission or acceptance.

First-party Python code is released under the [MIT license](LICENSE); see
[third-party and data exclusions](THIRD_PARTY_NOTICES.md).
