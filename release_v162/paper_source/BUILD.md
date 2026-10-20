# V162 manuscript source

Build from this directory with TeX Live and latexmk:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error main.tex
```

The bibliography is `references.tex`; no private data, model or network access
is needed. The package includes IEEEtran, the author-supplied vector Figure 1,
and the CTAN cmap files with their notices. Keep cmap before fontenc and retain
`glyphtounicode` and `pdfgentounicode=1`. The local `ot1.cmap` changes only the
math hat's text mapping from ASCII U+005E to modifier circumflex U+02C6; the
rendered glyph is unchanged. The already-correct summation/brace mapping remains.

The PDF has four technical pages and one references-only page with all 35 entries.
Font sizes, margins, author order, affiliations, grants and Figure 1 are retained.
The funding body's established acronym NSFC is used in the acknowledgment.
Checkmark component columns and the abstract GitHub link are retained.

V162 makes the n-gram count and training-fold RMS domain explicit, reconciles
within-study policy cost differences with a distinct unweighted subset profile,
and describes the actual rounded FLEURS gains and empty-candidate provenance.
The five original FLEURS gains round to 0.37 pp; H3 differs by two edits on one
trigger. They are not an exact common-output identity.

The additional H4+e diagnostic refits all five coefficients on existing complete
HF-expanded DEV, with the original five component folds and 49 penalties.
All 735 CV and three final fits converged. Its CV27 complete-policy WER is
31.52351688586994%, and it retains all 18 empty acceptances. This retrospective
diagnostic neither replaces G4 nor inherits the original confirmation identity.

Table I retains the original frozen panel. The full-precision N+R/S+R value is
32.75476627936039%, correctly displayed as 32.75%; contrasts use unrounded values.
Direct and Native confirmation reconstructions remain post-lock diagnostics.
H4/HWR4 cannot be reconstructed from only the persisted selected outputs.

Table III separates study A (four paths, three checkpoints, three paired rounds)
from study B (seven paths, one checkpoint, three paired rounds). Both use the
existing 727-recording stratified sample. V162 performs no new GPU timing.
Added study-B differences are strategy contrasts, not isolated stage times.
The separate fixed 25-recording CV27 profile is unweighted and includes two
records that skip scoring; it is not an exclusively active subset.

The realized sample misses five FLEURS and 207 CV27 later-checkpoint trigger
instances. Their latency impact is unknown. Small trigger rates and agreement
between cost studies do not establish a millisecond bound. Observed peak allocated
memory was measured with both models resident, not as a standalone deployment
footprint. Complete H4/H3/HWR4/H4+e and trigger-selective PLL costs are unmeasured.

All empty TEST candidates originate from final HF outputs, but the generating
termination/no-speech branch was not logged. The fixed nonempty guard and B
reversion are identical on these caches. No short-speech safety or no-speech
causal mechanism is inferred. Window-local analyses remain cached diagnostics.

Only the main PDF is the formal conference submission candidate. The private
author return and numerical archive are not conference supplementary material.
Code and anonymous numerical materials are indexed separately at
https://github.com/Zhifan-Pan/ISCAS2027. Formal submission remains the author's
decision; this revision produces no acceptance score or guarantee.
