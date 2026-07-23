# Configure And Build

Longform Kit keeps shared publication settings in Git and machine-specific
citation paths out of Git. There is no setup program or symlink layer.

## Configure Citations

In Zotero with Better BibTeX installed, export the collection for the document
using **Better CSL JSON** and enable **Keep updated**. Save the export at a
stable location outside the repository. Install or download the CSL style that
the document should use.

Create `_quarto.yml.local` in the project root:

```yaml
bibliography: /home/you/Documents/zotero-exports/project-library.json
csl: /home/you/Zotero/styles/chicago-fullnote-bibliography.csl
```

Use absolute paths. On Windows, forward slashes are the least surprising YAML
form, for example `C:/Users/you/Documents/library.json`. The bibliography must
be a CSL JSON export, not the Zotero data directory or `zotero.sqlite`.

Dependent CSL styles refer to a separate parent style. Prefer a self-contained
style, or keep the required parent style installed and available beside the
selected style. If Pandoc cannot resolve a parent style, select the independent
parent or download a self-contained style from the Zotero style repository.

`_quarto.yml.local` is ignored because it contains personal paths. Configure it
separately on every machine and in CI.

## Edit The Manuscript

Edit descriptive metadata in `writing/manuscript/metadata.yml`:

```yaml
lang: en-GB

book:
  title: "A Longform Document"
  subtitle: "An optional subtitle"
  author: "Author Name"
  date: today
  output-file: "longform-document"
```

Edit the reading order in `writing/manuscript/chapters.yml`:

```yaml
book:
  chapters:
    - index.md
    - writing/manuscript/chapters/01-introduction.md
    - writing/manuscript/chapters/02-conclusion.md
    - writing/manuscript/bibliography.md
```

Keep `index.md` first and edit `writing/manuscript/front-matter.md` instead of
the root adapter. Front matter may begin with an unnumbered heading or remain
headingless. Keep `writing/manuscript/bibliography.md` where the generated
bibliography should appear, normally last.

Write active chapters under `writing/manuscript/chapters/`. Use
`writing/drafts/`, `writing/notes/`, and `writing/planning/` for writing that is
not part of the rendered manuscript. Put figures and attachments in
`materials/` and refer to them with project-root paths.

## Configure Publication Settings

Shared Quarto, PDF, and DOCX defaults live in root `_quarto.yml`. Committed
document-specific overrides live in `_quarto-custom.yml`, which the root file
activates as the `custom` profile. Machine-specific paths remain in
`_quarto.yml.local`.

Core publishing behaviour lives outside `publishing/features/`, is registered
in root `_quarto.yml`, and remains enabled in an unchanged checkout. Optional
features live in named directories under `publishing/features/`, are not
auto-discovered, and are activated only by copying their documented snippets
into `_quarto-custom.yml`. See the
[optional-feature catalogue](../publishing/features/README.md).

The starter PDF uses KOMA-Script's exact 140 by 227 mm type area on mirrored A4
pages, approximately 15.25/19.3 EB Garamond body typography, 12.7/16 notes,
microtype, and two-line widow and orphan control. Its one-up publication target
is PDF/A-4f. The second PDF preserves these pages and places two consecutive
pages on each landscape A4 sheet, but makes no PDF/A or PDF/UA claim. Read
`style/typography.md` for the design policy and
[Customize the project](customization.md) before changing the implementation.

All headings are unnumbered by default. The table of contents includes chapter
headings only. Editorial conventions live in `style/editorial.md`; executable
filters, DOCX processing, and tests live in `publishing/`.

## Build Every Format

Run the canonical build from the project root:

```sh
quarto run publishing/longform.ts build
```

One invocation creates the complete set, using `book.output-file` from
`writing/manuscript/metadata.yml`:

```text
output/longform-document.pdf
output/longform-document-2up.pdf
output/longform-document.docx
output/longform-document.md
```

The build program renders the PDF and DOCX as combined Quarto books. It derives
the two-up PDF with `pdfjam`, placing source pages as `[blank | 1]`, `[2 | 3]`,
`[4 | 5]`, and so on. It reads the source outline with qpdf, then runs two
LuaLaTeX passes to restore discovery metadata, document language, and bookmarks
remapped to the imposed sheets. Print that file at one PDF page per physical
sheet; it is sequential spread imposition, not booklet or signature imposition.
Because imposition discards the source structure tree, this print derivative
remains untagged and makes no PDF/A or PDF/UA conformance claim.

For GFM, the program resolves the chapter list into a temporary standalone
Quarto document, renders it through Pandoc, extracts referenced media, and
removes the temporary source. This preserves citations, includes, shortcodes,
and `when-format="gfm"` conditionals.

Plain `quarto render` is useful for diagnosis but is not the production build:
it does not create the imposed PDF and combined Markdown edition in one run.

`PDFJAM`, `QPDF`, and `LUALATEX` may name alternate executables.

A release can make one-up validation fail closed by setting
`LONGFORM_VALIDATE_PDF=1`; the build then requires veraPDF through
`QUARTO_VERAPDF` or `PATH` and validates the profiles declared by the effective
`pdf-standard` configuration. Routine builds do not invoke the validator. The
KOMA-compatible PDF-management override and future PDF/UA route are documented
in [`publishing/pdf/standards/README.md`](../publishing/pdf/standards/README.md).

## Check The Result

The build command fails if a required output is missing or empty. It also
sanitizes generated DOCX package metadata with
`publishing/docx/sanitize.lua`. The DOCX table of contents remains a live Word
field; Word updates it when fields are refreshed, while simpler previewers may
initially show only the contents heading. To cache entries and page numbers in
a release build, activate the optional DOCX TOC feature and run with
LibreOffice Writer, Python UNO, and `LONGFORM_REFRESH_DOCX_TOC=1`; see the
[optional-feature catalogue](../publishing/features/README.md).

For layout changes, inspect both PDFs and the DOCX rather than relying only on
exit status. Chapters should start on rectos in the source PDF. The first
two-up sheet should be blank on the left with the title on the right, and later
rectos should also occupy right-hand slots.

Run the integration test after build, configuration, filter, or reference-DOCX
changes:

```sh
python3 publishing/tests/test_build.py
python3 publishing/tests/test_optional_features.py
```

Useful Quarto diagnostics are:

```sh
quarto check
quarto inspect
```

Never patch files under `output/`. Fix the Markdown, Quarto configuration,
citation input, filter, or `publishing/docx/reference.docx`, then rebuild.

## Run The Linters

Install whichever configured tools suit your workflow:

```sh
vale sync
vale writing/manuscript
harper-cli lint -d british -u .harper/dictionary.txt \
  writing/manuscript/*.md writing/manuscript/chapters/*.md
markdownlint-cli2 README.md "docs/**/*.md" "writing/**/*.md" "style/**/*.md"
```

The Harper dictionary starts empty. Add only accepted names and specialist
terms from the manuscript, not vocabulary from Longform Kit documentation or
publishing code. Linters provide evidence, not editorial authority. Do not
rewrite quotations, citation keys, or deliberate specialist language merely to
silence a warning.
