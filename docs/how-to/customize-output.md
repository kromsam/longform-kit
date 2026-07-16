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

Preserve the styles used by the filters, including `Epigraph Text`,
`Epigraph Source`, `TOC Heading`, and `Bibliography`.

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

Run the affected build and inspect the result visually after every layout
change.
