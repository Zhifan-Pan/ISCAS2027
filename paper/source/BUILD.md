# Submission manuscript source

Build from this directory with:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The result contains four body pages, including acknowledgment, and a fifth page
containing only references. The bibliography is maintained in references.tex.
No BibTeX run, network connection, dataset or model is needed to build.

IEEEtran conference mode uses US Letter. Body, abstract, caption, table and
reference font settings, margins, column widths and baseline spacing are unchanged.
Standard flushbottom aligns the first seven body columns. The final body column
uses raggedbottom. Table I row spacing is unchanged. Figure 1 remains a vector
image in a double-column float, scaled to 0.64 textwidth to accommodate the
explicit acceptance definitions and expanded analysis.

The manuscript includes Equations (1)--(3), a single argmax operator, and
references [1]--[33]. Preserve the local CMap and math-unicode files.
Original experimental values are unchanged. Table IV adds baseline WERs from
existing counts, and the text reports a separate CPU RMS sensitivity analysis.
The unnumbered RankNet objective supplements numbered Equations (1)--(3).

Format maintenance: retains IEEEtran paragraph elasticity. Two Introduction
paragraphs use looseness=1 for line breaking only. hyperref draft mode disables
PDF hyperlinks per ISCAS 2027 PDF requirements while retaining printed URLs.
This is not IEEEtran draft mode. These settings preserve font sizes and baselines.
