# V165 extended corpus header rules

The six rules below FLEURS and CV27 in Tables II, III and IV are slightly
longer, with symmetric endpoints and a clear gap between corpus groups.
Column centering, two-row header alignment, text positions and pagination
are unchanged. The source diff changes only three cmidrule lines.

- [Manuscript PDF](manuscript_v165.pdf)
- [Matching source ZIP](source_v165.zip) and [source tree](paper_source/)
- [Diff against the preceding centered tables](source.diff)
- [Build instructions](paper_source/BUILD.md)
- [Preceding snapshot](../release_v165_centered_tables/)

All scientific text, numbers, captions, authors, Figure 1 and 35 references
are unchanged. The PDF retains four technical pages and one references-only
page, with the same font sizes and margins. Compilation reports no LaTeX
warnings or overfull/underfull boxes. All word coordinates are identical to
the preceding snapshot. Only six horizontal rules change in the drawing
comparison. No scientific experiment was performed.

Run `python verify_release.py` to verify snapshot byte identity. Private
author notes, reviews, task prompts and credentials are excluded. Earlier
snapshots remain unchanged. No formal conference submission was performed.
