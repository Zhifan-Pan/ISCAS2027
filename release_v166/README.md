# V166 final sentence revisions

This snapshot applies the requested sentence edits to the V165 figure-symbol snapshot, using the author's selected five-page wording. It retains four technical pages and one page of references. The latest update removes the dataset release-date phrase from Section III, with no change to the experimental data or analyses.

- [Manuscript PDF](manuscript_v166.pdf)
- [Matching source ZIP](source_v166.zip) and [source tree](paper_source/)
- [Diff for the latest wording update](source.diff)
- [Previous snapshot](../release_v165_figure_symbols/)

The revised text links the two cost studies, reports the existing checkpoint contrasts, distinguishes the 25-recording profile from population estimates, and explains the shared scoring pipeline. Reference [35] uses the name Seamless Communication Team. Author order remains Zhifan Pan, Maihemuti Maimaiti, Yingxiong Gao, Yuhui Ming, Aishan Wumaier.

Only main.tex, results.tex and references.tex change. All four tables, the two-column Figure 1, other paragraphs, scientific results and layout commands are unchanged. Pages 1 and 2 render identically to V165. Additional text changes natural line wrapping on later pages.

To build with pdfLaTeX and latexmk:

```sh
mkdir -p build
cd paper_source
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=../build main.tex
```

The compiled document is build/main.pdf. The included vector figure PDF makes SVG conversion unnecessary. The source ZIP contains the identical paper_source files under source/.

Run `python verify_release.py` to check file hashes. This checks snapshot integrity, not scientific correctness.

No training, inference, GPU timing, bootstrap, confirmation or model review was run for V166. Algorithmically identical triggered operations do not imply strictly identical measured wall-clock time. Sharing a scoring architecture is not an additional measured H4/HWR4 or selective-PLL timing result. Original scientific code and anonymous inputs remain in [V160](../release_v160/), with subsequent diagnostics in their respective snapshots.

Private author records, task prompts, screenshots, reviews and credentials are excluded. Prior snapshots are retained. No formal conference submission was performed.
