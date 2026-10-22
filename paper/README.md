# Final manuscript

- [Submission PDF](Selective%20Recovery%20for%20Multilingual%20ASR%20-%20Candidate%20Acquisition%20and%20Acceptance.pdf)
- [LaTeX source](source/) and [source archive](source.zip)
- [Evidence map](EVIDENCE.md) and [revision audit](REVISION_AUDIT.md)

## Build

Run from the repository root:

```sh
latexmk -cd -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir=../build paper/source/main.tex
```

The compiler output is `paper/build/main.pdf`; temporary build files stay in
the same Git-ignored directory. The submission PDF linked above is named after
the title. The source archive includes [standalone build instructions](source/BUILD.md).
The manuscript has four main-content pages and references only on page 5.
Table I separates the locked-panel macro WER summary (B) from paired contrasts
(C), with matching three-column layouts. Table II separates its comparison families.
Table IV presents Calls and Gain in five columns; full baseline WERs and the
exact RMS rules remain available in the linked evidence and audit.
The supplied vector figure and CMap files require no conversion or network access.

## Verify

Run from the repository root:

```sh
python3 paper/verify_release.py
python3 paper/verify_aggregates.py
python3 paper/verify_revision_evidence.py
python3 paper/evidence/gate_audit/verify_gate_audit.py --repo .
```

These verify file identity, source ZIP contents and aggregate arithmetic, not
new training, bootstrap inference or GPU timing. See the repository README for
scientific replay instructions. The PDF and source archive contain the current
final manuscript.
Local checks confirm embedded fonts, no PDF hyperlinks or bookmarks, and no
layout overflows. These checks do not replace IEEE PDF eXpress certification.
Historical experiment identifiers inside immutable records are provenance,
not alternative manuscript versions.
