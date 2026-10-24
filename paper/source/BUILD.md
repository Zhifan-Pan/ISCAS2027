# Submission manuscript source

Build from this directory with:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir=../build main.tex
```

The PDF and temporary build files are written to `../build/`. Building does not
overwrite the title-named submission PDF or mix generated files with the source.
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
Table I separates its locked-panel macro WER summary and paired contrasts into
three-column panels B and C. Table II separates the two comparison families.
Table I begins the left column of page 3, with Table II at the top of the right column.
Table IV reports Calls and Gain in five columns; baseline WERs remain in the
repository evidence. Section II-C gives inline RankNet probabilities and
edit-gap weights; Section IV-C reports the CPU RMS sensitivity analysis.

Format maintenance: retains IEEEtran paragraph elasticity. The related-work
paragraph uses looseness=1 for line breaking only. hyperref draft mode disables
PDF hyperlinks per ISCAS 2027 PDF requirements while retaining printed URLs.
This is not IEEEtran draft mode. These settings preserve font sizes and baselines.
