# Configuration Reference

`document/_quarto.yml` is the public project configuration. Paths are relative
to `document/`.

## Project

```yaml
project:
  type: longform-kit
  output-dir: build
```

Keep `type: longform-kit` so Quarto loads the vendored project extension. Build
outputs must remain separate from source files.

## Book

```yaml
book:
  title: "A Longform Document"
  subtitle: "Optional subtitle"
  author: "Author Name"
  date: today
  date-format: "D MMMM YYYY"
  output-file: "longform-document"
  chapters:
    - index.qmd
    - manuscript/01-introduction.md
    - references.md
```

`output-file` is a basename without an extension. `chapters` is the ordered
source-of-truth list used by every output and by Zettlr synchronization.

## Citations And Structure

```yaml
bibliography: references/library.json
csl: references/style.csl
lang: en-GB
toc-title: Contents
toc-depth: 2
number-sections: true
link-citations: true
```

Longform Kit requires exactly one project-local CSL JSON bibliography.
`toc-depth` is the fallback depth for the DOCX and GFM TOCs; use the dedicated
longform keys below when those outputs need different depths. `link-citations`
applies to the native Quarto outputs. Markdown-derived GFM overrides it to
`false`; LaTeX-derived GFM requires it to be explicitly `false` so already
rendered citeproc notes survive the LaTeX-to-Markdown round trip reliably.

## Longform Metadata

```yaml
longform:
  student-number: ""
  degree-title: ""
  supervisor: ""
  institute: ""
  bibliography-pagebreaks: 1
  gfm-source: markdown
  gfm-toc-depth: 2
  gfm-legacy-plain-scalars: false
  docx-toc-depth: 2
  docx-toc-switches: "h z u"
  docx-toc-heading-pagebreak: false
  docx-toc-leading-blank: false
  docx-bibliography-leading-blank: false
  preserve-attached-note-positions: false
  required-fonts: []
```

The first four values extend the PDF and LaTeX title page when non-empty.
The remaining values control build compatibility:

| Key | Default | Purpose |
| --- | --- | --- |
| `bibliography-pagebreaks` | `1` | Number of explicit DOCX page breaks inserted before the bibliography |
| `gfm-source` | `markdown` | Use ordered Markdown sources, or set `latex` to convert the canonical LaTeX build |
| `gfm-toc-depth` | `toc-depth` | Override the GFM table-of-contents depth |
| `gfm-legacy-plain-scalars` | `false` | Preserve YAML implicit scalars without quoting in LaTeX-derived GFM for byte-level legacy parity |
| `docx-toc-depth` | `toc-depth` | Override the Word TOC field's heading depth |
| `docx-toc-switches` | `h z u` | Select the Word TOC field switches for hyperlinks, Web Layout, and outline levels |
| `docx-toc-heading-pagebreak` | `false` | Insert a page break at the start of the DOCX TOC heading |
| `docx-toc-leading-blank` | `false` | Insert an empty `Normal` paragraph before the DOCX TOC |
| `docx-bibliography-leading-blank` | `false` | Insert an empty `First Paragraph` before the generated bibliography entries |
| `preserve-attached-note-positions` | `false` | Keep a citation note before immediately following punctuation when the source citation is attached to the preceding word |
| `required-fonts` | `[]` | Font family names that `doctor` must resolve with `fc-match` |

Use positive integers for TOC depths. `bibliography-pagebreaks` is a
non-negative integer. `docx-toc-switches` accepts only `h`, `z`, and `u`,
separated by spaces or commas. Compatibility flags are strict booleans. Use
`preserve-attached-note-positions` only when reproducing an established note
placement convention; ordinary Pandoc citation spacing remains the default.
Keep `gfm-legacy-plain-scalars` disabled unless a frozen GFM baseline requires
values such as numbers or booleans to remain unquoted; enabling it can change
their parsed YAML types.

When `required-fonts` is non-empty, `bin/longform doctor` also requires
Fontconfig and fails if a requested family resolves to a substitute. Declare
production fonts here when silent substitution would change pagination.

## Formats

```yaml
format:
  longform-kit-pdf: default
  longform-kit-docx: default
  longform-kit-latex: default
```

Do not add GFM here. Quarto book projects do not support a combined GFM target;
`bin/longform build gfm` supplies that output through Quarto's bundled Pandoc
using the source selected by `longform.gfm-source`.

Format-specific overrides may replace `default` with a mapping. Keep the custom
format names so the shared filters and assets remain active.

## Binding Profile

`document/_quarto-binding.yml` overrides PDF layout options such as geometry.
The wrapper derives the binding filename from `book.output-file` and appends
`-binding`, so the profile does not declare a second output name.
