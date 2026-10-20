# V164 paper and source snapshot

This editorial revision retains the author-supplied, two-column arrow-aligned
Figure 1 while correcting six mathematical labels to match the manuscript.
All 35 references, three method equations, table data, original models and
statistical scopes are retained. The PDF contains four technical pages and
one references-only page. See [BUILD.md](paper_source/BUILD.md).

- [Manuscript PDF](manuscript_v164.pdf)
- [Complete source ZIP](source_v164.zip) and [source tree](paper_source/)
- [Source diff](source.diff)
- [Arithmetic summary](arithmetic_summary.json)

V164 introduces no training, candidate inference, GPU timing, confirmation
study or bootstrap. It clarifies existing rounded contrasts, FLEURS macro
aggregation, and the difference between population-weighted strategy costs
and the separate 25-recording profile. The all-25 profile includes two
scoring-skipped singletons. Small trigger fractions do not establish a
deterministic latency-error bound; four-feature architectural reuse is not
an independent full-policy cost measurement.

The frozen acquisition-control results retain their original scope. The
Direct comparison is post-lock, the refitted acceptors use development-exposed
TEST, and the fixed empty guard is a cached sensitivity diagnostic. Equal
rounded gains are not proof of identical candidate selection. No new
confirmation identity is assigned to later policies.

Inherited executable scientific code and anonymous inputs remain in
[V160](../release_v160/), the H4+e and cost audits in [V162](../release_v162/),
and the post-lock confirmation interval in [V163](../release_v163/). Historical
releases are unchanged. The current arithmetic file verifies inherited
results and does not replace those inputs or masquerade as a new experiment.

Run `python verify_release.py` here to verify file integrity. This check does
not establish scientific independence or conference acceptance. The source
ZIP rebuild has been compared to the delivered PDF page by page: text and
rendered pixels match, with no LaTeX box or citation warnings.

Private author notes, task instructions, reviews, credentials, raw audio and
reference text are excluded. Only the main PDF is the formal submission
candidate; formal submission has not been performed.
