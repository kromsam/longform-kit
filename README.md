# Longform Kit

Longform Kit is an opinionated, reproducible authoring project for theses,
dissertations, books, and reports. Write Markdown in Zettlr, organize the work as
a Quarto book, render it with Pandoc, and manage references in Zotero.

The tools have distinct jobs:

- **Zettlr** is the writing and project-navigation interface.
- **Quarto** owns the chapter order, shared metadata, and book builds.
- **Pandoc** parses Markdown, processes citations, applies Lua filters, and writes
  the output formats.
- **Zotero with Better BibTeX** owns bibliographic metadata and exports the
  project-local CSL JSON file.
- **`bin/longform`** gives people and AI agents one deterministic command surface.

## Quick Start

Requirements:

- Quarto 1.9.38 through 1.9.x
- LuaLaTeX, normally supplied by TeX Live or MacTeX
- Fontconfig's `fc-match` when `longform.required-fonts` is configured
- EB Garamond for the intended DOCX typography; Word substitutes another font
  when it is unavailable
- Zettlr and Zotero with Better BibTeX for the intended authoring workflow

Create a project from the public starter:

```sh
quarto use template kromsam/longform-kit
cd YOUR-PROJECT
bin/longform setup
bin/longform doctor
bin/longform build all
```

Edit document metadata and chapter order in
[`document/_quarto.yml`](document/_quarto.yml). Write front matter in
[`document/index.qmd`](document/index.qmd), chapters in `document/manuscript/`,
and citations with Pandoc keys such as `[@exampleBook2024, 42]`.

Generated files appear in `document/build/`:

```text
longform-document.pdf
longform-document-binding.pdf
longform-document.docx
longform-document.tex
longform-document.md
longform-document-latex/
```

The exact basename comes from `book.output-file` in `_quarto.yml`; the binding
PDF adds the `-binding` suffix automatically.

## Commands

```sh
bin/longform setup
bin/longform build [all|pdf|docx|latex|gfm]
bin/longform check
bin/longform lint
bin/longform doctor
bin/longform zettlr [sync|install]
```

Run `check` before sharing or submitting a document. It validates the project,
chapter list, local CSL file, bibliography structure, citation keys, semantic
epigraphs, and the generated Zettlr project file.

PDF, DOCX, and LaTeX use Quarto's combined book pipeline. Quarto does not support
combined GFM book output, so Longform Kit provides two explicit GFM sources.
The default `markdown` mode asks `quarto inspect` for the ordered chapters and
runs Quarto's bundled Pandoc with the project filters and citation data. The
optional `latex` mode renders the canonical LaTeX output first and converts that
file to GFM for compatibility with workflows whose semantics live in the LaTeX
export. LaTeX-derived GFM requires `link-citations: false` for a reliable
citeproc round trip. See [Architecture](docs/explanation/architecture.md) and
[Compatibility](docs/reference/compatibility.md).

## Documentation

- [First document tutorial](docs/tutorial/first-document.md)
- [How-to guides](docs/how-to/)
- [Configuration and command reference](docs/reference/)
- [Architecture and reproducibility](docs/explanation/)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

Longform Kit is licensed under the MIT License. Bundled third-party material has
its own terms; see [Third-Party Notices](THIRD_PARTY_NOTICES.md).
