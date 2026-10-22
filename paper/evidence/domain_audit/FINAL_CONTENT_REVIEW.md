# Independent final content review

Scope: second-round changes to `main.tex` and `results.tex` against the preserved
second-round baseline; checked against gate replay and empty-algebra evidence.
No manuscript was changed by this review.

## Material finding resolved

The Conclusion now separates the evidence scopes explicitly:
"On the locked panel, selective acquisition matches unconditional recovery
across seeds. Separate timing studies show lower recovery cost."
The locked-panel accuracy result is no longer conflated with Study A/B timing.
No material issue remains from this bounded content review.

## Verification of the four requested repairs

- The deterministic preference for HF-proposed zero-feature empty outputs is
  explicit, with fitted coefficient signs and a distinction from normalized
  empty text. The 18-acceptance guard, 91.52% retention and limited DEV empty
  calibration remain. No claim is made that every empty proposal is proven to
  originate from a particular no-speech branch.
- Offline word-repetition and token-ID compression gate call rates and
  positive-edit-gain retention match `../gate_audit/SUMMARY.csv`, with the
  original gate as comparator. The paragraph explicitly says cached banks.
- "Zero-shot acoustic transfer" is immediately qualified by CV27 DEV selector
  training. Acoustic and orthographic mismatch are framed as possible
  contributors whose effects were not isolated.
- Direct is a trigger-time simplification with comparable accuracy; its
  advantage is attributed to checkpoint one. HWR4's advantage over H4 is
  attributed to checkpoint two and explicitly limited in the Conclusion.

The G4 table cell is `33.98`, and the two alleged punctuation errors are absent.
`primary.tex`, `acceptors.tex`, `cost.tex`, `language_scope.tex`, and
`references.tex` are byte-identical to the second-round baseline. No new
scientific finding is inferred from the baseline's unchanged sections.

## Reviewed file identities

- `main.tex`: `1b09a5c498d923a0b9ea0ea0df6d1ca6ff3436bd0a973969bb9121fd38e1740e`
- `results.tex`: `c9e4dba1721f0220f64f0070c376a53d7284aff9cc98d0d28ba82c5b5cb02e96`
