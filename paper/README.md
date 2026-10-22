# Final manuscript

- [Submission PDF](Selective%20Recovery%20for%20Multilingual%20ASR%20-%20Candidate%20Acquisition%20and%20Acceptance.pdf)
- [LaTeX source](source/) and [source archive](source.zip)
- [Evidence map](EVIDENCE.md) and [revision audit](REVISION_AUDIT.md)

## Build

```sh
cd paper/source
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error main.tex
```

Run these commands from the repository root. The compiler output is
`paper/source/main.pdf`; the submission PDF linked above is named after the title.
The manuscript has four main-content pages and references only on page 5.
The supplied vector figure and CMap files require no conversion or network access.

## Verify

```sh
python3 paper/verify_release.py
python3 paper/verify_aggregates.py
python3 paper/verify_revision_evidence.py
```

These verify file identity, source ZIP contents and aggregate arithmetic, not
new training, bootstrap inference or GPU timing. See the repository README for
scientific replay instructions. The PDF and source archive contain the current
final manuscript.
Local checks confirm embedded fonts, no PDF hyperlinks or bookmarks, and no
layout overflows. These checks do not replace IEEE PDF eXpress certification.
Historical experiment identifiers inside immutable records are provenance,
not alternative manuscript versions.
