# How The Pieces Fit Together

Longform Kit adds Quarto because Zettlr and Quarto solve different problems.
Neither replaces the other.

## Zettlr Is The Writing Environment

Zettlr opens the Markdown files, provides a project view, helps insert Zotero
citations, and supports an author-focused editing workflow. Its project file is
useful UI state, but it is not the canonical build manifest.

Depending on global Zettlr export profiles would make the document depend on one
machine's home directory and GUI settings. Longform Kit therefore generates
`.ztr-directory` from the repository configuration and sends canonical builds
through the CLI.

## Quarto Is The Project And Build Layer

Pandoc converts documents well, but it does not itself define a durable
multi-chapter project. Quarto adds:

- An ordered book manifest in `_quarto.yml`.
- Project-wide metadata and format options.
- Combined chapter rendering.
- Local, versioned project-type extensions.
- Profiles such as the binding PDF layout.
- A machine-readable resolved configuration through `quarto inspect`.
- A pinned bundled Pandoc.

This is the reason for introducing Quarto: it replaces bespoke shell assembly,
copied defaults, absolute paths, and GUI-only export state with a documented
project model. Authors do not need to adopt Quarto as their editor.

## Pandoc Is The Document Engine

Pandoc parses every source into an abstract syntax tree. Citeproc and the
Longform Kit Lua filters transform that tree before a writer produces PDF,
LaTeX, DOCX, or Markdown. Semantic Divs let one source express an epigraph or
page break without embedding four output-specific implementations.

## Zotero Is The Bibliographic Authority

Zotero owns editable item metadata. Better BibTeX exports a project collection
to CSL JSON, and the exact CSL file controls citation rendering. Both files are
committed, so a build reads them locally and does not need Zotero.

## The CLI Is The Stable Contract

`bin/longform` is intentionally smaller than the tools beneath it. People, CI,
Zettlr, and AI agents all invoke the same validation and build operations.

The flow is:

```text
Zettlr edits Markdown
        |
        v
_quarto.yml orders the project
        |
        v
Quarto combines the book and invokes Pandoc
        |
        v
Lua filters + citeproc transform the AST
        |
        +----> PDF / binding PDF / DOCX / LaTeX
        |
        +----> canonical LaTeX ----> GFM compatibility mode
```

GFM is one explicit exception. Quarto books cannot render a combined GFM file,
so the wrapper uses Quarto's bundled Pandoc outside the combined book writer.
The default `longform.gfm-source: markdown` path asks `quarto inspect` for the
resolved order and processes those sources with the project metadata, citation
data, and filters. It preserves GFM-specific conditional content and is the
normal authoring path.

The optional `gfm-source: latex` path first refreshes the canonical LaTeX build
and converts that file. It exists for established projects whose accepted GFM
output depends on transformations already expressed in the LaTeX export. Since
citeproc has already rendered notes and bibliography entries, the conversion
requires `link-citations: false` rather than trying to reconstruct citation
semantics a second time. This remains one authoring model with two deliberate
conversion boundaries, not two competing source trees.
