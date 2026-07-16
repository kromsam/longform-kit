# Customize Outputs

Prefer project configuration over editing the vendored extension. This keeps
upgrades reviewable and separates a document's design from toolkit internals.

## Change The Output Name

Set a filename-safe basename without an extension:

```yaml
book:
  output-file: "my-dissertation"
```

The CLI uses this basename for every output and appends `-binding` to the
binding PDF automatically. Do not duplicate `book.output-file` in the binding
profile.

## Override PDF Options

Add overrides beneath the custom PDF format:

```yaml
format:
  longform-kit-pdf:
    mainfont: "EB Garamond"
    sansfont: "Fira Sans"
    fontsize: 12pt
    linestretch: 1.25
  longform-kit-docx: default
  longform-kit-latex: default
```

The selected fonts must be installed on every rendering machine. Keep ordinary
page geometry in `_quarto.yml` and binding geometry in
`_quarto-binding.yml`. The `format` map is the complete output list, so retain
the DOCX and LaTeX entries when overriding PDF options.

Declare fonts that must not be substituted:

```yaml
longform:
  required-fonts:
    - EB Garamond
    - Fira Sans
```

`bin/longform doctor` then uses Fontconfig's `fc-match` to verify each family.
Keep this list empty when a project's typography permits local substitution.

The built-in PDF and LaTeX formats set `colorlinks: false` for print-friendly
links. Override that value explicitly when a screen-first edition should use
colored links.

## Customize DOCX Styles

Copy the extension's reference document to a project-owned location, edit its
named Word styles, and point the format at that copy:

```yaml
format:
  longform-kit-pdf: default
  longform-kit-docx:
    reference-doc: assets/reference.docx
  longform-kit-latex: default
```

Preserve the styles used by the filters, including `Epigraph Text`, `Epigraph
Text Flush`, `Epigraph Source`, `First Paragraph`, `TOC Heading`, and
`Bibliography`.

## Add Title Metadata

Standard title fields live under `book`. Longform-specific PDF title fields
live under `longform`:

```yaml
longform:
  student-number: "12345678"
  degree-title: "MA Thesis"
  supervisor: "Dr Example"
  institute: "Example University"
  bibliography-pagebreaks: 1
```

`bibliography-pagebreaks` controls the DOCX page breaks inserted immediately
before the bibliography. The other fields extend the PDF and LaTeX title page.

## Choose The GFM Source

Markdown is the normal GFM source and preserves GFM-specific conditional
content:

```yaml
longform:
  gfm-source: markdown
  gfm-toc-depth: 2
```

For a migrated project whose accepted Markdown export depends on its canonical
LaTeX representation, select the compatibility path:

```yaml
longform:
  gfm-source: latex
  gfm-toc-depth: 2
link-citations: false
```

The LaTeX path refreshes the `.tex` build first and refuses to run while
citation links are enabled. It resolves format conditionals for LaTeX, so do not
use it for content that must be selected specifically with
`when-format="gfm"`.

## Reproduce An Established DOCX Layout

Use dedicated controls instead of changing the global TOC or inserting raw
OpenXML into the manuscript:

```yaml
longform:
  docx-toc-depth: 1
  docx-toc-switches: "h"
  docx-toc-heading-pagebreak: true
  docx-toc-leading-blank: true
  docx-bibliography-leading-blank: true
  preserve-attached-note-positions: true
```

The blank-paragraph and attached-note settings are compatibility switches, not
recommended defaults. Enable them only after comparing against an established
DOCX. Configure individual epigraph spacing and styles with the semantic
attributes in [Semantic Markdown](../reference/semantic-markdown.md).

Run the affected build and inspect the result visually after every layout
change.
