# V163 manuscript source

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
Font sizes, margins, author details, affiliations, grants and all numerical results are retained.
Figure 1 uses the author's final-gi SVG update, included unchanged alongside its
vector PDF. It is placed across both columns on page 2 at 0.80 textwidth, with the
author's caption. Double-column float separation is set before `maketitle` so
IEEEtran computes title spacing consistently. Redundant wording and table row
padding were reduced to keep four technical pages; no results or references
were removed. The three method equations are unchanged. The figure locally
preserves its existing PDF transparency group, avoiding a duplicate /Group
dictionary injected by recent pdftex.def versions.
At the author's request, Yingxiong Gao now precedes Yuhui Ming; all other author positions and markers are unchanged.
The acknowledgment spells out National Natural Science Foundation of China in full, at the author's request.
Checkmark component columns and the abstract GitHub link are retained.

V163 connects the within-study strategy cost differences to the results prose,
reports a post-lock Direct-minus-S+R paired interval, and distinguishes findings
consistent across the three observed seeds from checkpoint-concentrated effects.
The n-gram count, RMS domain, centered empty-hypothesis margin and recording-level
Direct definition remain unchanged. The five original FLEURS gains round to
0.37 pp; H3 differs by two edits on one trigger, so rounded gains do not establish
identical selected outputs.

The inherited V162 H4+e diagnostic refitted all five coefficients on existing complete
HF-expanded DEV, with the original five component folds and 49 penalties.
All 735 CV and three final fits converged. Its CV27 complete-policy WER is
31.52351688586994%, and it retains all 18 empty acceptances. This retrospective
diagnostic neither replaces G4 nor inherits the original confirmation identity.
Its duplicate rounded table row is now summarized in Section IV-D. No fitting
or GPU measurement was repeated for V163.

Table I retains the original frozen panel. The full-precision N+R/S+R value is
32.75476627936039%, correctly displayed as 32.75%; contrasts use unrounded values.
Direct and Native confirmation reconstructions remain post-lock diagnostics.
V163 adds one locked descriptive comparison: Direct minus S+R is -0.04817099 pp,
with a two-sided 95% percentile interval [-0.19082464, +0.04051922] from 10,000
within-language speaker-cluster draws synchronized across the three checkpoints.
The original statistical families are unchanged. Crossing zero does not prove
equivalence. H4/HWR4 require full candidate features beyond the archived scores
and transcripts; their reported refit results use the development-exposed TEST.

Table III separates study A (four paths, three checkpoints, three paired rounds)
from study B (seven paths, one checkpoint, three paired rounds). Both use the
existing 727-recording stratified sample. V163 performs no new GPU timing.
Added study-B differences are strategy contrasts, not isolated stage times.
The separate fixed 25-recording CV27 profile is unweighted and includes two
records that skip scoring; it is not an exclusively active subset.

The realized sample misses five FLEURS and 207 CV27 later-checkpoint trigger
instances, or 0.05% and 0.12% of all checkpoint-recording instances. Matching
expanded candidate banks does not establish equal independently measured wall
time or a deterministic error bound on a population latency ratio. Observed peak allocated
memory was measured with both models resident, not as a standalone deployment
footprint. Complete H4/H3/HWR4/H4+e and trigger-selective PLL costs are unmeasured.

All empty TEST candidates originate from final HF outputs. The fixed nonempty
guard and B reversion are identical on these caches: 91.52% of the original CV27
gain survives, at 31.88% WER. Excluding empty outputs does not remove all word
deletions or identify the acoustic cause of empty outputs. Window-local analyses
remain cached diagnostics.

Only the main PDF is the formal conference submission candidate. The private
author return and numerical archive are not conference supplementary material.
Code and anonymous numerical materials are indexed separately at
https://github.com/Zhifan-Pan/ISCAS2027. Formal submission remains the author's
decision; this revision produces no acceptance score or guarantee.
