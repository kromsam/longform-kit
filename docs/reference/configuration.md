# Configuration Reference

Root `_quarto.yml` is the public project configuration. All paths are relative
to the repository root.

## Project And Book

```yaml
project:
  type: book
  output-dir: build

book:
  title: "A Longform Document"
  author: "Author Name"
  output-file: "longform-document"
  chapters:
    - index.md
    - document/manuscript/01-introduction.md
    - document/references.md
```

Keep `project.type: book`. `index.md` must remain first and is generated; edit
`document/front-matter.md` instead. `book.chapters` is authoritative for every
output and for Zettlr synchronization.

## Citations And Structure

```yaml
bibliography: references/library.json
csl: references/style.csl
lang: en-GB
toc: true
toc-title: Contents
toc-depth: 2
number-sections: true
link-citations: true
```

Longform Kit requires exactly one CSL JSON bibliography. Quarto and its bundled
Pandoc process citations and generate the bibliography natively.

## Longform Checks

Only two wrapper-specific settings remain:

```yaml
longform:
  gfm-toc-depth: 2
  required-fonts:
    - EB Garamond
```

`gfm-toc-depth` defaults to the top-level `toc-depth`. `required-fonts` is an
optional list of exact families that `bin/longform doctor` must resolve with
Fontconfig before production rendering.

## Native Formats

```yaml
format:
  pdf:
    pdf-engine: lualatex
    geometry: "twoside,left=36mm,right=36mm"
    include-in-header:
      - file: _extensions/epigraph/epigraph.tex
  docx:
    toc: true
    reference-doc: references/reference.docx
  latex:
    include-in-header:
      - file: _extensions/epigraph/epigraph.tex
```

These are ordinary Quarto format names and options. Do not add GFM to this map:
Quarto book projects do not support one combined GFM output, so
`bin/longform build gfm` uses a temporary standalone Quarto render.

Root `_quarto-binding.yml` overrides only binding-specific PDF options. The CLI
derives the binding filename from `book.output-file` and appends `-binding`.
