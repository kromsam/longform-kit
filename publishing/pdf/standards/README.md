# Core PDF Standards Compatibility

The one-up Longform Kit publication PDF uses LuaLaTeX, KOMA-Script, and the
core type area. Root `_quarto.yml` targets PDF/A-4f by default through LaTeX's
dedicated, non-tagging `pdfmanagement` package. The imposed two-up proof is
deliberately untagged and makes no PDF/A or PDF/UA claim.

## Why Quarto's Metadata Partial Is Overridden

Quarto normally translates `pdf-standard` into `\DocumentMetadata` before the
document class. Beginning with LaTeX 2025-11-01, that command loads `latex-lab`
tagging support even when tagging is off. LaTeX provides
`\RequirePackage{pdfmanagement}` followed by
`\SetKeys[document/metadata]{...}` for PDF management without the tagging
layer; this route is documented in [latex3/pdfresources issue 101][pdfresources-101].

That distinction matters because current KOMA classes and `tocbasic` remain
incompatible with LaTeX tagging. Tagging can remove table-of-contents link
annotations, fail to represent headings semantically, and change page
composition. Relevant upstream records include [tagging-project issue
88][tagging-88], [issue 1118][tagging-1118], the open `tocbasic` [issue
701][tagging-701], and [Quarto issue 14422][quarto-14422].

`document-metadata.latex` replaces only Quarto's partial of the same name. It
runs before `\documentclass`, as `pdfmanagement` requires, and leaves the rest
of Quarto's maintained template intact. The partial rejects every PDF/UA
request with an actionable error until the incompatibility is resolved.

Root `_quarto.yml` keeps `pdf-standard` as a list. Compatible standards may be
union-added by a custom profile because [Quarto profile arrays are
union-concatenated][quarto-profiles]; PDF/UA is not compatible on this path.

## Validation

Ordinary builds remain possible without a strict external gate. CI and release
builds set `LONGFORM_VALIDATE_PDF=1`; `publishing/longform.ts` then derives the
veraPDF profiles from effective configuration and fails if the verifier is
missing, produces no compliance result, or reports non-compliance. PDF/A-4f
maps to veraPDF profile `4f`.

## Route To PDF/UA

Two future routes remain viable:

1. Wait until KOMA sectioning, title/front-matter handling, and `tocbasic` are
   listed as compatible by the official [LaTeX tagging status table][status],
   then verify heading structure, reading order, annotations, notes, and the
   complete publication layout.
2. Port the design to the compatible standard `book` class, replacing KOMA
   font, section, footnote, contents, and type-area interfaces with tagging-safe
   equivalents. Avoid currently incompatible packages such as `titlesec`,
   `titletoc`, and `tocloft`.

A veraPDF pass alone is not an adoption gate. A PDF/UA migration must also
preserve visual composition and produce a correct semantic structure and
reading order. The `epigraph` paragraph-boundary limitation remains recorded
in [tagging-project issue 455][tagging-455], while the legacy footnote/floats
socket used by core typography follows [issue 78][tagging-78].

[pdfresources-101]: https://github.com/latex3/pdfresources/issues/101#issuecomment-3204847179
[tagging-88]: https://github.com/latex3/tagging-project/issues/88#issuecomment-2195087095
[tagging-1118]: https://github.com/latex3/tagging-project/issues/1118#issuecomment-3628861575
[tagging-701]: https://github.com/latex3/tagging-project/issues/701
[quarto-14422]: https://github.com/quarto-dev/quarto-cli/issues/14422
[quarto-profiles]: https://quarto.org/docs/projects/profiles.html
[status]: https://latex3.github.io/tagging-project/tagging-status/
[tagging-455]: https://github.com/latex3/tagging-project/issues/455
[tagging-78]: https://github.com/latex3/tagging-project/issues/78#issuecomment-4467134590
