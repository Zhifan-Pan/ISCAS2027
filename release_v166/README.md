# V166 final manuscript

This snapshot includes the final sentence revisions and table spacing refinements. It retains four technical pages and one page of references.

- [Manuscript PDF](manuscript_v166.pdf)
- [Matching source ZIP](source_v166.zip) and [source tree](paper_source/)
- [Diff for the latest table spacing update](source.diff)
- [V165 figure snapshot](../release_v165_figure_symbols/)

All four tables use centered columns with symmetric 4 pt outer padding. The last numeric columns and their headings have space before the right ends of the horizontal rules. Existing vertical header alignment and corpus group rules are retained. The update affects only primary.tex, acceptors.tex, cost.tex and language_scope.tex. Table content, results, font sizes, row heights, Figure 1 and body text are unchanged. Pages 1, 2 and 5 render identically to the preceding V166 snapshot.

Earlier V166 edits link the two cost studies, report existing checkpoint contrasts, distinguish the 25-recording profile from population estimates and explain the shared scoring pipeline. The dataset paragraph omits release-date wording. Reference [35] uses Seamless Communication Team. Author order remains Zhifan Pan, Maihemuti Maimaiti, Yingxiong Gao, Yuhui Ming, Aishan Wumaier.

To build with pdfLaTeX and latexmk:

```sh
mkdir -p build
cd paper_source
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=../build main.tex
```

The compiled document is build/main.pdf. The included vector figure PDF makes SVG conversion unnecessary. The source ZIP contains the identical paper_source files under source/.

Run `python verify_release.py` to check file hashes. This checks snapshot integrity, not scientific correctness.

No training, inference, GPU timing, bootstrap, confirmation or model review was run for V166. Algorithmically identical triggered operations do not imply strictly identical measured wall-clock time. Sharing a scoring architecture is not an additional measured H4/HWR4 or selective-PLL timing result. Original scientific code and anonymous inputs remain in [V160](../release_v160/), with subsequent diagnostics in their respective snapshots.

Private author records, task prompts, screenshots, reviews and credentials are excluded. Prior versions remain in Git history. No formal conference submission was performed.
