# Longform Kit

Longform Kit is an opinionated, reproducible authoring project for theses,
dissertations, books, and reports. Write ordinary Markdown in Zettlr, organize
the work as a Quarto book, render it with Pandoc, and manage references in
Zotero.

The tools have distinct jobs:

- **Zettlr** is the writing and project-navigation interface.
- **Quarto** owns metadata, chapter order, citations, and native book builds.
- **Pandoc**, bundled with Quarto, parses Markdown and writes the outputs.
- **Zotero with Better BibTeX** owns bibliographic metadata and exports the
  project-local CSL JSON file.
- **`bin/longform`** gives people, CI, and AI agents one deterministic command
  surface.

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
- Zettlr and Zotero with Better BibTeX for the intended authoring workflow

Start a project from this repository. On GitHub, use the **Use this template**
button to create your own copy, or clone it directly:

```sh
git clone https://github.com/kromsam/longform-kit YOUR-PROJECT
cd YOUR-PROJECT
bin/longform setup
bin/longform doctor
bin/longform build all
```

Edit the manuscript metadata (title, author, date, language) in
[`document/metadata.yml`](document/metadata.yml) and the chapter order in
[`document/chapters.yml`](document/chapters.yml). Write the preface in
[`document/front-matter.md`](document/front-matter.md), chapters in
`document/manuscript/`, and citations with Pandoc keys such as
`[@exampleBook2024, 42]`. The root [`index.md`](index.md) is a one-line Quarto
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
