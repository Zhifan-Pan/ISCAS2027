# V165 manuscript and matching source

This editorial revision improves sentence flow and organizes Section IV-D into
four thematic paragraphs. It preserves all numerical table entries, checkmarks,
method equations, 35 references and the author-supplied two-column Figure 1.
The PDF has four technical pages and one references-only page.

- [Manuscript PDF](manuscript_v165.pdf)
- [Complete source ZIP](source_v165.zip) and [source tree](paper_source/)
- [Source diff against V164](source.diff)
- [Build instructions](paper_source/BUILD.md)

No training, inference, GPU timing, confirmation or bootstrap was rerun for
V165. Scientific code and anonymous numerical inputs remain in the earlier
[V160](../release_v160/), [V162](../release_v162/) and [V163](../release_v163/)
snapshots. The original confirmation applies to the original frozen policy.
Later acceptor, gate and window diagnostics keep their retrospective scope.
Cost Study A covers four paths and three checkpoints; Study B covers seven
paths and one checkpoint. The profile averages all 25 recordings, including
two singleton cases. A small trigger count fraction alone does not prove a
bound on relative latency error.

The source ZIP was independently rebuilt and all five pages matched the
final PDF in extracted text and rendered pixels. The final logs contain no
LaTeX box or citation warnings. Run `python verify_release.py` to check file
identity; integrity checks do not establish scientific correctness or venue
acceptance. Formal submission remains the author's decision.

Private author notes, editorial instructions, reviews, credentials, raw audio
and reference texts are excluded. Only the main PDF is a formal submission
candidate. Earlier releases are unchanged.
