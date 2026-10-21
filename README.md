# Selective Recovery for Multilingual ASR: Candidate Acquisition and Acceptance

This repository accompanies the final ISCAS manuscript. It provides one
submission PDF, matching LaTeX source, scientific code and anonymous numeric
inputs for reproduction.

## Paper

- **[Final paper PDF](paper/Selective%20Recovery%20for%20Multilingual%20ASR%20-%20Candidate%20Acquisition%20and%20Acceptance.pdf)**
- [LaTeX source](paper/source/) · [Download source ZIP](paper/source.zip)
- [Build instructions](paper/README.md) · [Claim and evidence map](paper/EVIDENCE.md)

The PDF contains four pages of main content and one page of references.

## Repository guide

| Directory | Contents |
| --- | --- |
| `paper/` | Final manuscript, source and aggregate evidence |
| `experiments/` | Candidate acquisition, acceptor fitting, audio inference and measured costs |
| `empty_candidate_diagnostic/` | H4+e refits and empty-output controls |
| `confirmation_diagnostic/` | Post-lock paired confirmation diagnostic and numeric replay |
| `reproduction/` | Portable inference dependencies, configurations and original numeric inputs |
| `matched_cost_evidence/` | Matched-runtime measurements and output/RNG checks |

## Verify and reproduce

```sh
python3 verify_repository.py
python3 paper/verify_aggregates.py
```

The first command checks artifact hashes and the source archive. The second
checks aggregate arithmetic. Neither launches model inference, fitting,
bootstrap inference or GPU timing.

For scientific reproduction, start with [the experiment guide](experiments/REPRODUCE.md).
[Audio inference](experiments/README.md#audio-inference) requires independently
obtained audio and model assets. The [empty-candidate guide](empty_candidate_diagnostic/README.md)
and [confirmation guide](confirmation_diagnostic/REPRODUCE.md) describe optional CPU replay.
Use new output directories and the recorded environments; do not overwrite
published fitted models or evidence.

## Evaluation scope

The locked 7,500-recording confirmation panel evaluates acquisition under the
original fixed G4 selector. Direct reconstruction, refitted selectors and
TEST comparisons are retrospective. Cost Study A measures four paths across
three checkpoints; Study B measures seven paths on one checkpoint. Their
estimates retain separate scopes. Selective PLL remains future work.

Original experiment identifiers inside protocols, scripts and result records
are preserved for traceability. They do not denote additional paper versions.
Raw audio/reference text, model weights and credentials are not distributed.
Publication of this repository does not imply conference acceptance.

## License

First-party Python code uses the [MIT license](LICENSE). See
[third-party notices and data exclusions](THIRD_PARTY_NOTICES.md) for manuscript,
figure, template, dependency and dataset licensing.
