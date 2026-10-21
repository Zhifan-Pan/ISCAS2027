# Build the final manuscript

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error main.tex
```

Run in this directory with TeX Live and latexmk installed. The output is
`main.pdf`: four pages of main content followed by one references-only page.
The bibliography is maintained in `references.tex`, with 33 references.
IEEEtran, the double-column vector figure and CMap files are included.
Preserve the Unicode mapping preamble and local CMap files.

This package contains no audio, model weights or experimental logs.
Scientific code and numeric replay inputs are available at
https://github.com/Zhifan-Pan/ISCAS2027.
