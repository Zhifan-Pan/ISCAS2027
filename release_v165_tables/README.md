# V165 table layout update

This version aligns all four tables to the IEEE column width, centers column
headings and checkmarks, and aligns numerical entries. Confirmation results,
contrasts and S/D/I diagnostics use independent column layouts within their
original tables. Font sizes and all numerical values are unchanged.

- [Manuscript PDF](manuscript_v165.pdf)
- [Complete source ZIP](source_v165.zip) and [source tree](paper_source/)
- [Table layout diff against the preceding V165](source.diff)
- [Build instructions](paper_source/BUILD.md)
- [Preceding V165 prose revision](../release_v165/)

The PDF has four technical pages and one references-only page. All table
values, checkmarks, labels and captions retain their original content.
The body, equations, figure, authors and references are unchanged. Pages
1, 2 and 5 render identically to the preceding V165. The source ZIP was
independently rebuilt and all five pages match the delivered PDF in text
and rendered pixels. The logs contain no LaTeX box or citation warnings.

No training, inference, GPU timing, confirmation or bootstrap was run.
The original confirmation and retrospective analyses retain their existing
scope. Study A covers four paths and three checkpoints, whereas Study B
covers seven paths and one checkpoint. This change makes no new scientific
claim or runtime measurement. Formal submission remains the author's decision.

Run `python verify_release.py` to check snapshot byte identity. Private
editorial notes, reviews, task instructions and credentials are excluded.
Only the main PDF is a formal conference submission candidate. Earlier
release snapshots remain unchanged.
