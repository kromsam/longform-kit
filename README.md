# Longform Kit

Longform Kit is an opinionated authoring project for theses, dissertations,
books, and reports. Write ordinary Markdown in Zettlr, organize the work as a
Quarto book, render it with Pandoc, and manage references in Zotero.

The tools have distinct jobs:

- **Zettlr** is the writing and project-navigation interface.
- **Quarto** owns metadata, chapter order, citations, and native book builds.
- **Pandoc**, bundled with Quarto, parses Markdown and writes the outputs.
- **Zotero with Better BibTeX** owns bibliographic metadata and keeps an
  external Better CSL JSON export current.
- **`bin/longform`** gives people, CI, and AI agents one deterministic command
  surface and links each checkout to its local Zotero files.

`document/` is deliberately reserved for author-owned content: the manuscript
Markdown, `document/metadata.yml` (title, author, date, language, and other
descriptive metadata), and `document/chapters.yml` (the chapter order). Quarto
configuration, generated state, references, extensions, scripts, and outputs all
live at the repository root.

## Quick Start

Requirements:

- Quarto 1.9.38 through 1.9.x
- LuaLaTeX, normally supplied by TeX Live or MacTeX
- Fontconfig's `fc-match` when `longform.required-fonts` is configured
- Zotero with Better BibTeX to maintain the citation export
- Zettlr for the intended authoring interface

Before setup, export the relevant Zotero library or collection with the
**Better CSL JSON** translator and **Keep updated** enabled, then install the
desired style in Zotero. See [Connect a Zotero
collection](docs/how-to/use-zotero.md) for the complete setup.

Start a project from this repository. On GitHub, use the **Use this template**
button to create your own copy, or clone it directly:

```sh
git clone https://github.com/kromsam/longform-kit YOUR-PROJECT
cd YOUR-PROJECT
bin/longform setup
bin/longform doctor
bin/longform build all
```

`setup` asks for the Better CSL JSON export location, the active Zotero data
directory, and an installed citation style by title, CSL ID, or filename. The
export location may be the exact file or a directory containing
`library.json`. It is not the Zotero data directory or `zotero.sqlite`. Setup
creates ignored live links under `references/`; it does not copy or commit the
library or style. Run it on every machine and in CI.
Citation output is therefore not Git-pinned: Better BibTeX or Zotero style
updates can affect a build without changing the repository.

For unattended setup, pass all three values explicitly:

```sh
bin/longform setup \
  --library FILE_OR_DIR \
  --zotero-data-dir DIR \
  --style TITLE_OR_ID_OR_FILENAME
```

Point Zettlr's citation preferences manually to the resolved export file. When
`--library` names a directory, that file is its `library.json`.

Edit the manuscript metadata (title, author, date, language) in
[`document/metadata.yml`](document/metadata.yml) and the chapter order in
[`document/chapters.yml`](document/chapters.yml). Write the preface in
[`document/front-matter.md`](document/front-matter.md), chapters in
`document/manuscript/`, and citations with Pandoc keys such as
`[@yourCitationKey, 42]`. The root [`index.md`](index.md) is a one-line Quarto
adapter and is not an authoring file.

Keep figures and other attachments outside `document/`, for example under
`resources/`, and reference them with project-root paths such as
`![Description](/resources/figure.png)`. The leading slash is Quarto's
project-root syntax and remains stable in both book and combined GFM builds.

Generated files appear in `build/`:

```text
longform-document.pdf
longform-document-binding.pdf
longform-document.docx
longform-document.tex
longform-document.md
longform-document-latex/
```

## Commands

```sh
bin/longform setup
bin/longform build [all|pdf|docx|latex|gfm]
bin/longform check
bin/longform lint
bin/longform doctor
bin/longform zettlr [sync|install]
```

PDF, DOCX, LaTeX, citeproc, TOCs, reference-DOCX styling, conditional content,
and page breaks use native Quarto options. Epigraphs use the vendored
[Fancy Epigraphs](https://github.com/andrewheiss/fancy-epigraphs-quarto)
v0.0.1 shortcode. Quarto books do not produce a combined GFM file, so the one
small exception is `bin/longform build gfm`: it creates a temporary standalone
Quarto document, allowing Quarto to resolve includes, shortcodes, and
conditionals before writing `build/longform-document.md`. Referenced figures
are copied beside it under `build/longform-document_files/`.

## Documentation

- [First document tutorial](docs/tutorial/first-document.md)
- [How-to guides](docs/how-to/)
- [Configuration and command reference](docs/reference/)
- [Architecture and reproducibility](docs/explanation/)
- [Release notes](https://github.com/kromsam/longform-kit/releases)
