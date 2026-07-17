# Configuration Reference

Root `_quarto.yml` is the public project configuration. All paths are relative
to the repository root.

## Project And Book

```yaml
project:
  type: book
  output-dir: build

metadata-files:
  - document/metadata.yml
  - document/chapters.yml

book:
  output-file: "longform-document"
```

Keep `project.type: book`. The `metadata-files` entries pull the author-owned
manuscript metadata and chapter list in from `document/`; only structural build
settings such as `book.output-file` stay in `_quarto.yml`.

## Manuscript Metadata

The manuscript's descriptive metadata lives beside the authored content in
`document/metadata.yml` and is merged into the configuration through
`metadata-files`:

```yaml
lang: en-GB

book:
  title: "A Longform Document"
  subtitle: "A reproducible Zettlr, Quarto, Pandoc, and Zotero project"
  author: "Author Name"
  date: today
  date-format: "D MMMM YYYY"
```

These are ordinary Quarto keys, so `date: today` resolves to the build date.
Setting them here is equivalent to setting them in `_quarto.yml` directly.

## Chapter List

The ordered chapter list lives in `document/chapters.yml`, merged into `book:`
the same way. It is authoritative for every output and for Zettlr
synchronization:

```yaml
book:
  chapters:
    - index.md
    - document/manuscript/01-introduction.md
    - document/references.md
```

`index.md` must remain first and is generated; edit `document/front-matter.md`
instead. Keep `document/references.md` at the intended bibliography position.

## Citations And Structure

```yaml
bibliography: references/library.json
csl: references/style.csl
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
