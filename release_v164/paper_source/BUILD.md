# V164 manuscript source

Build with TeX Live and latexmk from this directory:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error main.tex
```

The package contains the complete source, IEEEtran, vector Figure 1 as SVG and
PDF, and CTAN cmap files with their notices. No private data, models, network
access or BibTeX run is required. The bibliography is `references.tex`.
Keep cmap before fontenc, `glyphtounicode` and `pdfgentounicode=1`. The local
`ot1.cmap` maps the math hat to U+02C6 without changing its rendered glyph.

There are four technical pages and one references-only page, with all 35
references retained. Template font sizes, margins, affiliations and grants
are unchanged. Yingxiong Gao precedes Yuhui Ming as requested by the authors;
the corresponding author remains second. The acknowledgment uses National
Natural Science Foundation of China in full.

Figure 1 retains the author's arrow-aligned artwork across both columns on
page 2 at 0.80 textwidth. Six labels now match the paper: candidates use y_ik,
the branches define C_i(0)=B_i and C_i(1)=F_i=B_i union {g_i}, and the recording
flag has superscript rec. Corrected labels have embedded fonts; other original
labels remain vector outlines. Geometry, colors, icons and arrows are unchanged.
The included PDF preserves its own transparency group; no regeneration is
needed to compile the manuscript.

V164 clarifies confirmation rounding, the two-edit FLEURS baseline difference,
population-weighted strategy costs versus a separate 25-recording profile,
and the deterministic nonempty guard. Equations (1)--(3), table data and fitted
models are unchanged. No training, inference, GPU timing or bootstrap was
performed for this revision. Full-precision frozen S+R WER is
32.75476627936039%, correctly displayed as 32.75%; contrasts use unrounded
means. Equal rounded FLEURS gains do not establish identical selected outputs.

Table III separates four-path/three-checkpoint Study A from
seven-path/one-checkpoint Study B. The 85.9 ms teacher-scoring and 149.3 ms PLL
profile means include all 25 recordings, with two scoring-skipped singletons.
They are neither population means nor means over only the 23 active cases.
Trigger-count fractions do not establish a deterministic latency-error bound;
shared scoring architecture is not an independent full-policy cost measurement.

Only the main PDF is the formal conference submission candidate. Internal
author notes and the retained research archive are not formal supplementary
material. Public code and numerical evidence are indexed at
https://github.com/Zhifan-Pan/ISCAS2027. Formal submission remains the author's
decision; compilation and code publication imply no acceptance guarantee.
