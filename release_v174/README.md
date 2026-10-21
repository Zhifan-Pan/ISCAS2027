# V174 manuscript and reproduction index

- [Manuscript PDF](manuscript_v174.pdf)
- [Source tree](paper_source/) and [source ZIP](source_v174.zip)
- [Evidence map and interpretation](EVIDENCE.md)
- [Compilation and presentation checks](CHECKS.json)

This snapshot consolidates the manuscript revisions after V166. It includes
the evidence distinctions and denominator explanations, 33 references, revised
academic prose, centered tables, the author's two-column vector Figure 1,
natural column flow, the restored dataset durations and recording counts, and
the Common Voice 27.0 (CV27) naming convention. The final packaging audit corrects
an outdated build document; it changes no manuscript text, equation, table,
figure or experimental value.

## Build

Install TeX Live with IEEEtran, pdfLaTeX and latexmk, then run:

```sh
cd paper_source
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error main.tex
```

The output is `paper_source/main.pdf`. The checked build has four main-content
pages and references only on page 5, with no overfull/underfull boxes, missing
characters or LaTeX warnings. The vector PDF is included, so SVG conversion is
unnecessary. Keep the supplied CMap files and preamble for math text extraction.
The source ZIP contains exactly the `paper_source/` files under `source/`.

## Verify

```sh
python3 verify_release.py
python3 verify_aggregates.py
```

The first command verifies file hashes and ZIP/source identity. The second
recomputes macro WER, non-Persian gains and positive-edit retention from the
included aggregate counts. These checks are arithmetic and artifact checks,
not independent replications or new statistical tests.

Scientific implementation, model fits and original anonymous replay inputs
remain in [V160](../release_v160/), [V162](../release_v162/) and
[V163](../release_v163/). The four aggregate evidence files were produced during
the earlier V168 audit of existing counts and are published here unchanged.
They contain language/seed totals rather than audio, reference text or personal
record identifiers. No new training, model inference, bootstrap or GPU timing
was run for this publication.

The locked confirmation covers the original G4 acquisition policy. Later refits,
Direct reconstruction and TEST comparisons retain their retrospective status.
Study A and Study B have different checkpoint scopes. The unweighted
25-recording stage profile includes two skipped singletons and is not a
population stage decomposition. Peak MiB denotes the observed maximum whole-call
CUDA allocation with both models resident, not an independent deployment
footprint. Selective PLL remains future work.
