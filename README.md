# Longform Kit

Longform Kit is a minimal, opinionated Quarto project for theses,
dissertations, books, and reports. Write Markdown, keep references in Zotero,
and produce the complete publication set with one command:

```sh
quarto run scripts/longform.ts build
```

Every build produces a one-sided, symmetric-margin PDF that retains blank
verso pages for recto chapter starts, a two-sided binding PDF with KOMA's
default mirrored margins and the same page sequence, a DOCX file, and one
combined GitHub Flavoured Markdown file. There is no setup command, generated
scaffolding, citation symlink, or LaTeX deliverable.

## Requirements

- Quarto 1.9.x
- A TeX distribution with LuaLaTeX, such as TeX Live or MacTeX
- Zotero with Better BibTeX for citation-library exports
- Zettlr if you want the optional writing interface
- Vale, Harper, or Markdownlint if you want prose and Markdown checks

## Start A Document

Clone the repository or create a repository from the GitHub template. Then:

1. Export the relevant Zotero library or collection with the **Better CSL
   JSON** translator and enable **Keep updated**.
2. Choose a CSL style file.
3. Create the ignored file `_quarto.yml.local` with the two absolute paths:

   ```yaml
   bibliography: /absolute/path/to/library.json
   csl: /absolute/path/to/style.csl
   ```

4. Edit the title, author, date, and language in `document/metadata.yml`.
5. Edit the ordered chapter list in `document/chapters.yml` and write the
   manuscript under `document/`.
6. Build everything:

   ```sh
   quarto run scripts/longform.ts build
   ```

The bibliography path is the Better CSL JSON export, not Zotero's data
directory or `zotero.sqlite`. The paths remain local to your machine; do not
commit `_quarto.yml.local`.

## Project Shape

- `_quarto.yml` contains the shared Quarto project and format configuration.
- `_quarto-binding.yml` contains only the binding-PDF overrides.
- `document/metadata.yml` contains manuscript metadata.
- `document/chapters.yml` defines the reading order.
- `document/front-matter.md`, `document/manuscript/`, and
  `document/references.md` contain author-owned prose.
- `references/reference.docx` defines the DOCX styles.
- `scripts/longform.ts` builds the complete output set and can generate the
  optional Zettlr project file.

Do not edit root `index.md`; it is Quarto's adapter for
`document/front-matter.md`. Keep figures and attachments outside `document/`,
for example under `resources/`, and use project-root paths such as
`![Description](/resources/figure.png)`.

## Outputs

The build command writes:

```text
build/longform-document.pdf
build/longform-document-binding.pdf
build/longform-document.docx
build/longform-document.md
```

Referenced media in the Markdown edition is extracted beside the Markdown
when necessary. PDF, binding PDF, and DOCX are native Quarto book renders. The
combined GFM edition is rendered from a temporary standalone Quarto document
so citations, shortcodes, includes, and format conditionals are resolved before
Pandoc writes Markdown. No temporary source or `.tex` file is retained.

## Optional Tools

Regenerate Zettlr's ignored project file after changing chapter order or
metadata:

```sh
quarto run scripts/longform.ts zettlr
```

Run the configured linters directly when installed:

```sh
vale sync
vale document
harper-cli lint -d british -u .harper/dictionary.txt document/*.md document/manuscript/*.md
markdownlint-cli2 README.md "docs/**/*.md" "document/**/*.md"
```

Treat prose-linter findings as editorial suggestions, especially in
quotations and specialist terminology.

## Guides

- [Configure and build](docs/configuration-and-building.md)
- [Use Zettlr](docs/zettlr.md)
- [Customize the project](docs/customization.md)
