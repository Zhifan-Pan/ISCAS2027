# Environment

The documented CPU replay environment is Python 3.10.12, NumPy 2.2.6 and SciPy
1.15.3. Dependencies are pinned in `requirements-cpu.txt`. Hash verification
uses only the Python standard library.

Audio inference additionally needs PyTorch, Transformers 4.57.6, original
Whisper/LoRA assets, XLM-R for PLL paths, audio dependencies and the existing
`reproduction/portable` helpers. The [historical dependency inventory](../reproduction/requirements-raw-recorded.txt)
records its original environment; this package does not claim a fresh GPU installation test.

The original R8 script retains a strict intermediate `1e-12` assertion that
has failed under Python 3.13 with NumPy 2.3.5. Preserve assertions and logs when
testing another environment. Build instructions are in [../paper/source/BUILD.md](../paper/source/BUILD.md).
