# Configure And Build

Longform Kit keeps shared project settings in Git and machine-specific
citation paths out of Git. There is no setup program and no symlink layer.

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
be a CSL JSON export – not the Zotero data directory and not `zotero.sqlite`.

Dependent CSL styles refer to a separate parent style. Prefer a self-contained
style, or keep the required parent style installed and available beside the
selected style. If Pandoc reports that it cannot resolve a parent style, select
the independent parent or download a self-contained style from the Zotero
style repository.

`_quarto.yml.local` is ignored because it contains personal paths. Configure it
separately on every machine and in CI.

## Edit The Manuscript

Edit descriptive metadata in `document/metadata.yml`:

```yaml
lang: en-GB

book:
  title: "A Longform Document"
  subtitle: "An optional subtitle"
  author: "Author Name"
  date: today
```

Edit the reading order in `document/chapters.yml`:

```yaml
book:
  chapters:
    - index.md
    - document/manuscript/01-introduction.md
    - document/manuscript/02-conclusion.md
    - document/references.md
```

Keep `index.md` first and edit `document/front-matter.md` instead of the root
adapter. Front matter may begin with an unnumbered heading or remain
headingless, as an epigraph often does; the adapter keeps a synthetic empty
heading out of the rendered document and table of contents. Keep
`document/references.md` where the generated bibliography should appear.

Shared Quarto, PDF, and DOCX defaults live in `_quarto.yml`. Committed
document-specific rendering overrides live in the active
`_quarto-custom.yml` profile. The PDF uses KOMA-Script's
`\areaset[current]{140mm}{227mm}`. The `current` argument keeps
the active binding correction while KOMA allocates the remaining page area.
The resulting vertical text-block margins are approximately 23.3 mm above and
46.7 mm below, with room for about 33 uninterrupted body lines. The block's
approximately 1:1.62 proportion contrasts with A4's 1:1.414 proportion while
retaining KOMA's 1:2 vertical margin relationship. Running heads and page
numbers occupy the surrounding page furniture rather than changing the
measure.

The PDF uses `twoside,openright` and fully mirrored pages. This retains blank
verso pages so every chapter starts on a recto. With the provisional
`BCOR=0mm`, rectos have an approximately 23.3 mm inner and 46.7 mm outer
margin, and versos reverse them. `BCOR` is the width of paper physically lost
in binding, not a decorative gutter. Replace zero only after the binding method
is known.

Bringhurst's A4 example on page 175 is already a two-sided construction: each
page has a spine margin of one unit and an outer margin of two, so the two
spine margins across an open spread together equal one outer margin. It does
not add a binding correction. The PDF reproduces the complete page-175
construction.

The project does not set Quarto's `geometry` option. `areaset` is KOMA-Script's
own interface for an exact type area, so KOMA still allocates and mirrors the
margins. The fixed type area applies consistently to the title, contents, and
manuscript body.

Bringhurst does not prescribe one universal body size: size, face, measure, and
leading have to work together. His conventional book measure is roughly 30
times the type size, with a practical range of about 20 to 40. At 15.25 pt, the
140 mm measure is about 26 times the nominal type size; the measured character
count below confirms that the combination is sound. KOMA receives the
non-standard size as `fontsize=15.25pt` in the PDF's class-option string.
Quarto's `fontsize` field would emit it as an ineffective bare option.

The PDF uses `linestretch: 1.055`. KOMA's native baseline at 15.25 pt is about
18.3 pt, so Pandoc and `setspace` produce an actual baseline of approximately
19.3 pt: effectively 15.25/19.3 typography. This proportionally scales the
earlier 12/15.2 setting with the text block. Bringhurst's examples include
12/15, and he advises adding lead as the measure grows.

Footnotes use 11.4 pt EB Garamond on a 15.25 pt baseline. This keeps them
clearly subordinate while giving the 140 mm note lines the generous leading
Bringhurst recommends. References remain superscript in the body, but KOMA's
`\deffootnote` gives each note a full-size label hung in a 1.5 em field. The
separator rule is suppressed; the ordinary footnote insertion space provides
the separation from the body. Long notes retain LaTeX's normal ability to
split across pages.

The layout figures were checked on a dense thesis PDF. Full justified body
lines were identified from their rendered bounds and counted with spaces and
punctuation. The old unpinned KOMA layout had a median of 99 characters per
full line; its central 80 per cent ran from 94 to 104. The faithful 140 mm
measure with proportionally scaled type had a median of 68 and an interquartile
range of 66–70, close to Bringhurst's 66-character ideal. In that manuscript,
the proportional type system produced 94 pages instead of 66 after the footnote
treatment was applied. No text box overflow was found.

All headings are unnumbered by default. The table of contents includes chapter
headings only; section and subsection headings remain in the document without
appearing in the contents.

The PDF maps its main, sans, and mono families to EB Garamond with
old-style figures, so body text, titles, headings, code, and page furniture use
one typeface. This deliberately makes code proportional. A downstream with
alignment-sensitive code can override `format.pdf.monofont` while retaining EB
Garamond elsewhere. LuaLaTeX applies its standard microtype support without
project-specific tuning. The `nowidow` package keeps at least two opening and
two closing lines of a paragraph together at page boundaries. These typography
choices, including the 11.4/15.25 footnote treatment, are preserved when the
PDF is imposed two-up. The tracked reference DOCX uses the same EB
Garamond policy for Latin text, and its body styles inherit Word's widow and
orphan control from the Normal style.

## Build Every Format

Run the canonical build from the project root:

```sh
quarto run scripts/longform.ts build
```

One invocation always creates the complete set:

```text
build/longform-document.pdf
build/longform-document-2up.pdf
build/longform-document.docx
build/longform-document.md
```

The PDF and DOCX are native combined Quarto book renders. The build program
derives the two-up PDF from the PDF with `pdfjam`, placing the
source pages as `[blank | 1]`, `[2 | 3]`, `[4 | 5]`, and so on. This makes the
title page and every recto the right-hand page of an A4 landscape sheet without
changing the source PDF's logical page parity. Print the two-up PDF at one PDF
page per physical sheet; do not apply the print dialog's pages-per-sheet option
again. This is sequential spread imposition, not booklet or signature
imposition for folded sheets.

GFM is the other derived case: the build program resolves the chapter list
into a temporary standalone Quarto document, renders it through Pandoc,
extracts referenced media, and removes the temporary source. This preserves
citations, includes, shortcodes, and `when-format="gfm"` conditionals without
keeping a LaTeX intermediate.

Plain `quarto render` is useful for diagnosis but is not the production build:
it cannot create the imposed PDF and combined GFM edition in one render.

## Check The Result

The build command fails if a required output is missing or empty. After
citation processing, it sanitizes the generated DOCX package: machine-local
bibliography and CSL properties and sample statistics inherited from the
reference DOCX are removed. An office application may calculate
layout-dependent statistics when it opens or saves the rendered document.
The DOCX table of contents is likewise a live field rather than a cached page
index. Microsoft Word refreshes it when fields are updated; previewers that do
not update Word fields may show only the contents heading until then.

For layout changes, also inspect both PDFs and the DOCX rather than relying on
exit status. Check the 140 mm measure, 227 mm depth, and mirrored 23.3/46.7 mm
margins in the PDF at `BCOR=0mm`. Chapters should begin on odd PDF pages. In
the two-up PDF, the first sheet should be blank on the left with
the title on the right; later rectos should also occupy right-hand slots. An
effective `geometry` value means the project has bypassed the KOMA type-area
policy.

Useful diagnostics are:

```sh
quarto check
quarto inspect
```

Do not patch files under `build/`; fix the Markdown, Quarto configuration, CSL
input, or `references/reference.docx` and rebuild.

## Run The Linters

The repository includes independent editor/CLI configuration for three tools.
Install whichever ones suit your workflow.

Vale supplies the tracked `Academic` house style and downloads proselint as a
low-authority advisory layer:

```sh
vale sync
vale document
```

Harper uses British English and the project dictionary at
`.harper/dictionary.txt`:

```sh
harper-cli lint -d british -u .harper/dictionary.txt document/*.md document/manuscript/*.md
```

Add only accepted names and specialist terms to that dictionary. Markdownlint
uses its Prettier-compatible style from the project root:

```sh
markdownlint-cli2 README.md "docs/**/*.md" "document/**/*.md"
```

Linters provide evidence, not editorial authority. Do not rewrite quotations,
citation keys, or deliberate specialist language simply to silence a warning.
