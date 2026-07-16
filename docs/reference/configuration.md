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

Version 1 requires exactly one project-local CSL JSON bibliography. `toc-title`
and `toc-depth` also configure the DOCX TOC field inserted by the Lua filter.

## Longform Metadata

```yaml
longform:
  student-number: ""
  degree-title: ""
  supervisor: ""
  institute: ""
  bibliography-pagebreaks: 1
```

The first four values extend the PDF and LaTeX title page when non-empty.
`bibliography-pagebreaks` is a non-negative integer used for DOCX pagination.

## Formats

```yaml
format:
  longform-kit-pdf: default
  longform-kit-docx: default
  longform-kit-latex: default
```

Do not add GFM here. Quarto book projects do not support a combined GFM target;
`bin/longform build gfm` supplies that output through the bundled Pandoc.

Format-specific overrides may replace `default` with a mapping. Keep the custom
format names so the shared filters and assets remain active.

## Binding Profile

`document/_quarto-binding.yml` overrides PDF layout options such as geometry.
The wrapper derives the binding filename from `book.output-file` and appends
`-binding`, so the profile does not declare a second output name.
