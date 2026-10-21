# V174 manuscript source

Build with TeX Live and latexmk in this directory:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error main.tex
```

The result is four pages of main content followed by references only on page 5.
The bibliography is maintained in references.tex; no BibTeX run, network access,
data or model is required. IEEEtran, Figure 1 and local CMap files are included.
Preserve cmap before fontenc, glyphtounicode, pdfgentounicode=1, ot1.cmap and
math-unicode.tex for math extraction.

V174 retains the V173 academic prose and layout, restores the dataset durations
and recording counts in Section III, and applies the requested sentence edits.
The first dataset mention is Common Voice 27.0 (CV27) in the abstract; subsequent
manuscript mentions use CV27. Original reference titles retain their wording.
The manuscript contains Equations (1)--(3) and references [1]--[33]. Authors,
affiliations, grants and evidence boundaries are preserved. Figure 1 remains the
author's symbol-synchronized vector artwork in a double-column float at 0.80 textwidth.
Its labels are outlined artwork; manuscript fonts are embedded with Unicode maps.

No experiment was run for this revision. Locked confirmation covers the original
G4 acquisition policy. Later refits and TEST comparisons remain retrospective,
including TEST access during development. Study A measures four paths across three
checkpoints; Study B measures seven on one checkpoint. The 25-recording profile
includes two skipped singletons and is not a population stage-time decomposition.
MiB measures maximum whole-call CUDA allocation over recordings and rounds,
including resident models.

The source ZIP contains the files needed for compilation under source/.
It does not contain datasets, model weights, historical author-return packages
or experimental logs. Scientific code and anonymous replay inputs are available
from https://github.com/Zhifan-Pan/ISCAS2027, with version-specific instructions.

Body text flows naturally between columns; there are no manual body column breaks.
The explicit page break before the bibliography keeps references on page 5.
Display, caption and float spacing retain the five-page layout with the existing
font sizes, margins and figure dimensions. The final packaging check changes only
this build document, not the manuscript source or PDF.
