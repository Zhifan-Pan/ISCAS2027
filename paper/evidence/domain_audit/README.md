# Domain and empty-candidate evidence audit

This CPU-only audit supplements the second manuscript revision. It performs no
ASR decoding or fitting and does not change a manuscript, table, or old result.

Reproduction from the repository root:

```sh
python3 paper/evidence/domain_audit/extract_domain_evidence.py --repo . --output paper/evidence/domain_audit
```

The optional `--history-root /home/mhmt_stu/Code/ISCAS2027_working_v63` repeats the
bounded local historical metadata search. That historical tree is not required
to reproduce the numerical DEV and feature audits from the public caches.

## CV27 DEV trigger census

`DEV_TRIGGER_RATES.csv` reports integer numerator and denominator for every
language and checkpoint. Each DEV checkpoint contains 58,171 unique recordings.
The existing recording-level trigger flags have totals 136, 64, and 241 for
checkpoints 101, 202, and 303. `DEV_TRIGGER_PROVENANCE.json` gives the input SHA256
hashes and aggregation definitions.

| Language | Trigger instances / seed-recordings | Pooled call rate (%) |
|---|---:|---:|
| Arabic | 6 / 30,813 | 0.019472300652322073 |
| Persian | 326 / 32,265 | 1.0103827677049435 |
| Polish | 83 / 30,288 | 0.27403592181722136 |
| Turkish | 14 / 35,592 | 0.039334681951000226 |
| Italian | 12 / 45,555 | 0.026341784655910437 |
| All recordings pooled | 441 / 174,513 | 0.2527032370081312 |

These pooled rates are not five-language macro averages. Language denominators
are identical across checkpoints, so pooled and mean-checkpoint rates coincide
up to floating-point representation within each language. The substantial
Arabic/Persian difference cautions against attributing concentration to UTF-8
encoding alone. It does not by itself identify acoustic or orthographic causes.

## Unadapted Whisper-small search

`BASE_MODEL_SEARCH.json` records the exact 533 text-metadata files inspected,
their hashes, excluded directory names, keyword expression, and all matches.
The scope includes the current repository's experiment and reproduction trees,
top-level historical metadata, `research_archive`, and the non-duplicated parts
of `acceptor_study_return` and `final_decision_return`. Build copies, reviewer
packages, and validation copies are excluded. No inspected file exceeded the
2 MB bound.

No unadapted Whisper-small WER or trigger-rate result was identified in that
scope. The one keyword match is
`reproduction/portable/vendor/audio_core.py:19`, which loads the base model;
line 20 immediately attaches the seed-specific LoRA adapter. Thus this match
does not establish an unadapted evaluation. The paper's `Raw top-1` is a decoding
policy of the adapted model, not the unadapted baseline. This search is not a
claim that no unadapted run exists anywhere on the server, in a compressed
archive, or under an unsearched filename/term.

## Empty-candidate algebra

`EMPTY_ALGEBRA_AUDIT.json` checks all nine DEV/CV27/FLEURS input files. For every
valid and fully observed raw feature vector with `t > 0`, `a <= 0`, `p <= 0`,
and `r >= 0` hold. There are zero nonnegative G4 scores for those vectors.
The frozen G4 coefficients have signs `(+,+,-,-)` in all three checkpoints.
Therefore a zero feature vector outranks every positive-token-length vector
under these coefficients. Subtracting the same top-beam feature vector, or
adding an ordinary candidate-independent intercept, cannot change this order.
An empty-specific feature `e(y)` can change it and is not an ordinary intercept.

The complete CV27 banks contain 6, 11, and 2 observed zero vectors. Of these,
6, 10, and 2 occur on triggered recordings, for 18 accepted proposals overall.
Thus "all 18 triggered empty proposals" must not be shortened to "all 18 empty
proposals in the complete unconditional cache," which actually has 19. No
observed zero vector appears in an original beam bank. The DEV banks contain
2, 1, and 2 zero vectors, all triggered. FLEURS has none.

The numeric cache stores missing body-token counts as `-1`, including HF
candidates. The audit consequently uses the observed log-length feature `t`,
not `body_tokens == 0`, to check the algebra. Raw text is not present in these
numeric files, and equality of normalized text to the empty string must not be
equated automatically with a zero feature vector. Singleton raw features that
were not observed are excluded from the feature checks.

## Boundaries of the supplied prose templates

- "Zero-shot" is valid only for transfer of the acoustic model/LoRA adapter:
  CV27 is excluded from LoRA adaptation, but the acceptance model is tuned on
  CV27 DEV. The entire system has not been developed without CV27 data.
- The data establish a cross-domain WER gap and repetition concentration, not
  separate causal contributions from crowdsourced noise, colloquial speech,
  script, orthography, and low-rank adaptation. Present those as plausible
  contributors, not measured causal findings. No unadapted comparator was
  identified by this audit.
- A configured no-speech threshold of 0.6 is not a per-instance record of the
  termination branch. Describe HF-proposed zero-feature empty outputs without
  claiming every one was demonstrably generated by that particular branch.
- The supplied template mistakenly assigns both acceptance effects to the
  second checkpoint. Existing `../acceptance_audit/CHECKPOINT_DIAGNOSTICS.json`
  places the Direct advantage in checkpoint 101 and the HWR4-over-H4 advantage
  in checkpoint 202. Their concentration should be stated separately.
- Direct skips additional scoring on triggered HF outputs but retains B on
  nontriggers. "Zero-rescoring alternative" without that qualification would
  misdescribe the complete policy.
- The four-language 0.61 pp / 0.45 pp gains alone do not establish statistical
  significance. The supplied phrase "statistically meaningful" needs a
  corresponding uncertainty calculation or should be omitted.
- Candidate repetition may be measured without decoding. Do not assert that
  an alternative gate misses subword/short-span loops until its actual missed
  cases are examined. The fixed 2.4 threshold was not selected by this audit.
