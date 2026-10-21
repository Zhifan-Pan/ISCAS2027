# V165 centered tables

This update centers every column in Tables I–IV, including row labels and
secondary panels. Acceptor, PLL, P, W, Path and Language span two header
rows and are vertically centered. Table III has separate rules below
FLEURS and CV27. Local booktabs spacing keeps the existing page flow.

- [Manuscript PDF](manuscript_v165.pdf)
- [Matching source ZIP](source_v165.zip) and [source tree](paper_source/)
- [Diff against the preceding table layout](source.diff)
- [Build instructions](paper_source/BUILD.md)
- [Preceding table layout](../release_v165_tables/)

All table values, checkmarks, captions, scientific prose, equations,
authors, Figure 1 and 35 references are unchanged. Original font sizes
and margins are retained. The PDF contains four technical pages and
one references-only page. No LaTeX box or citation warnings were found.
Pages 1, 2 and 5 render identically to the baseline. A clean rebuild of
the source ZIP matches all five delivered pages in text and pixels.

No training, inference, GPU timing, confirmation or bootstrap was run.
Existing scientific findings and limitations retain their original scope.
Formal submission remains the author's decision.

Run `python verify_release.py` to verify snapshot byte identity. Private
editorial records, reviews, task prompts and credentials are excluded.
Earlier release snapshots remain unchanged.
