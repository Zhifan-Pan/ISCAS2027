# Environment

The executed diagnostic used Python 3.13.12 and NumPy 2.5.3 on Linux x86-64,
with `OPENBLAS_NUM_THREADS=1` and `PYTHONDONTWRITEBYTECODE=1`.
No CUDA, GPU, neural model or SciPy operation is required for this script.
Version differences may affect byte-level metadata; use the recorded versions
when comparing the original numerical draws.

The manuscript uses pdfLaTeX and latexmk from TeX Live. IEEEtran, the vector
figure and the required CMap files/notices are shipped in `../paper/source/`.
`glyphtounicode` and the ordinary LaTeX packages must be available in TeX Live.
