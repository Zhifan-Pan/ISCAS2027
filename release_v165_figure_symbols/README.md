# V165 symbol-synchronized Figure 1

This snapshot replaces Figure 1 with the author-supplied symbol-synchronized
SVG and its vector PDF conversion. The diagram retains its two-column
placement, width, caption and size. The source and PDF preserve all four
tables, 35 references, authors, equations, numbers and scientific scope.

- [Manuscript PDF](manuscript_v165.pdf)
- [Matching source ZIP](source_v165.zip) and [source tree](paper_source/)
- [Figure SVG](paper_source/figures/Figure1_Vector.svg) and [vector PDF](paper_source/figures/Figure1_Vector.pdf)
- [Diff against the preceding table-rule snapshot](source.diff)
- [Build instructions](paper_source/BUILD.md)
- [Previous snapshot](../release_v165_table_rules/)

Only the two Figure1_Vector files change in the source tree. The manuscript
retains four technical pages and one references-only page without LaTeX
warnings or overfull/underfull boxes. Pages 1, 3, 4 and 5 match the previous
render exactly. Caption and body text on page 2 have identical coordinates.
The original SVG uses outlined lettering, which remains vector artwork
rather than searchable PDF text. No artwork content was edited.

The source ZIP was extracted and rebuilt. All 26 source files matched their
packaged copies, and every page matched the delivered manuscript render.
Run `python verify_release.py` to verify byte identity of this snapshot.
This checks file integrity rather than scientific correctness.

`tools/convert_user_figure1.py` exports a supplied SVG through librsvg/cairo.
It requires the system Python with PyGObject, librsvg and pycairo; a bundled
PDF is included so ordinary LaTeX compilation does not need these libraries.

No training, inference, GPU timing, bootstrap or confirmation experiment was
performed for this replacement. Original scientific code and anonymous
inputs remain in [V160](../release_v160/). Later refits do not inherit the
original confirmation. Private author notes, reviews, task prompts and
credentials are excluded. Earlier snapshots remain unchanged. No formal
conference submission was performed.
