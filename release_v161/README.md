# V161 manuscript layout update

V161 changes pagination and float placement only. Its words, equations,
checkmark ablations, numerical results, author information and original vector
figure are unchanged from V160. The manuscript has four technical pages and
one references-only page containing all 35 references.

- [Matching LaTeX source and build instructions](paper_source/BUILD.md).
- [Scientific code, frozen inputs, outputs and evidence scope](../release_v160/README.md).

The scientific release remains `release_v160/`, first published at commit
`8339110d6026b9709c18cc74b73cb5e9a26483ef`. No fitting, decoding, timing,
bootstrap or confirmation analysis was rerun for this layout update.

Tables II and III now follow their discussion at column bottoms. Body columns
use flush bottoms with modest elastic spacing, and complete bibliographic
entries are kept in one column. Template font sizes and margins are unchanged.

Verify this source snapshot without running any experiment:

```sh
python release_v161/verify_release.py
```

Private author-return materials, reviewer documents, raw audio, reference
transcripts and credentials are not part of this release. Publication here does
not represent a conference submission or an acceptance decision.
