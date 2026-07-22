# Longform Kit

Longform Kit is a minimal, opinionated Quarto project for theses,
dissertations, books, and reports. Write in Markdown, keep references in
Zotero, and produce the complete publication set with one command:

```sh
quarto run publishing/longform.ts build
```

Every build creates a PDF, a two-up PDF, a DOCX file, and one combined GitHub
Flavoured Markdown file. The default publication design uses EB Garamond,
mirrored A4 pages, an exact KOMA-Script type area, and PDF/A-4f for the one-up
publication PDF. See [`style/typography.md`](style/typography.md) for the design
policy and [Configure and build](docs/configuration-and-building.md) for its
implementation.

## Requirements

- Quarto 1.9.x
- A TeX distribution no older than June 2025, with LuaLaTeX and the
  `ebgaramond`, `etoolbox`, `microtype`, `nowidow`, and `tagpdf` packages;
  PDF management is supplied by the LaTeX core
- The LaTeX `epigraph` package when the bundled epigraph feature is enabled
- `pdfjam` from TeX Live for the two-up PDF
- Java 21 and veraPDF only for strict release validation
- Zotero with Better BibTeX for citation-library exports
- Zettlr if you want the optional writing interface
- Vale, Harper, or Markdownlint if you want prose and Markdown checks

## Start A Document

Clone the repository or create a repository from the GitHub template. GitHub's
template button creates a one-time snapshot; to retain shared ancestry and
merge later Longform Kit releases, follow the
[downstream maintenance guide](docs/downstream-maintenance.md). Then:

1. Export the relevant Zotero library or collection with the **Better CSL
   JSON** translator and enable **Keep updated**.
2. Choose a CSL style file.
3. Create the ignored file `_quarto.yml.local` with absolute paths to both:

   ```yaml
   bibliography: /absolute/path/to/library.json
   csl: /absolute/path/to/style.csl
   ```

4. Edit identity metadata and the output filename in
   `writing/manuscript/metadata.yml`.
5. Edit the reading order in `writing/manuscript/chapters.yml` and write
   chapters under `writing/manuscript/chapters/`.
6. Put committed document-specific rendering overrides in
   `_quarto-custom.yml`.
7. Build every output:

   ```sh
   quarto run publishing/longform.ts build
   ```

The bibliography path names the Better CSL JSON export, not the Zotero data
directory or `zotero.sqlite`. Keep citation exports outside the repository and
never commit `_quarto.yml.local`.

## Project Shape

```text
README.md
docs/

writing/
  manuscript/
    chapters/
    front-matter.md
    bibliography.md
    metadata.yml
    chapters.yml
  drafts/
  notes/
  planning/

materials/

style/
  editorial.md
  typography.md

publishing/
  longform.ts
  filters/front-matter.lua
  docx/reference.docx
  docx/sanitize.lua
  pdf/typography.tex
  features/README.md
  tests/

output/                 # generated and ignored

_quarto.yml
_quarto-custom.yml
index.md
```

The layout separates concerns:

- `writing/` contains all writing material. Only `writing/manuscript/` is an
  active rendering input by default.
- `materials/` contains figures, attachments, source material, feedback, or
  other document inputs that are not prose.
- `style/` states editorial and typographic policy. Executable filters,
  templates, and document conversion code belong under `publishing/`.
- `publishing/` contains the reusable rendering implementation and its tests.
- `publishing/pdf/` contains core PDF implementation enabled by root
  configuration. `publishing/features/` contains optional, explicitly
  activated extensions.
- `docs/` explains how to use and maintain the repository.
- `output/` contains generated deliverables and must not be edited or
  committed.

Root `_quarto.yml`, `_quarto-custom.yml`, and `index.md` stay at the project
root because Quarto discovers them there. Do not edit `index.md`; it is the
adapter for `writing/manuscript/front-matter.md`.

Use project-root paths for figures and attachments, for example
`![Description](/materials/figure.png)`, so all output formats resolve them
consistently.

## Core And Optional Features

Core behaviour lives outside `publishing/features/`, is registered in root
`_quarto.yml`, and is enabled in an unchanged checkout. Optional features live
in named directories under `publishing/features/`, are never auto-discovered,
and are activated only through a copied `_quarto-custom.yml` snippet.

The [optional-feature catalogue](publishing/features/README.md) defines the
documentation, activation, compatibility, failure, verification, ownership,
and licence contract for every bundled feature. It includes academic-title-page
and semantic-epigraph features. An empty custom profile enables none of them.

## Outputs

With the starter output name, the build command writes:

```text
output/longform-document.pdf
output/longform-document-2up.pdf
output/longform-document.docx
output/longform-document.md
```

The PDF and DOCX are native Quarto book renders. The one-up PDF targets
PDF/A-4f. The two-up PDF is imposed from it with a leading blank slot so rectos
appear on the right, but the imposed derivative makes no PDF/A or PDF/UA claim.
Print it at one PDF page per A4 sheet without applying another pages-per-sheet setting.
The combined Markdown edition resolves citations, shortcodes, includes,
conditional content, and referenced media before it is written. LaTeX is an
internal PDF concern, not a public output.

Strict PDF validation is explicit and offline after the validator is
installed:

```sh
LONGFORM_VALIDATE_PDF=1 \
  QUARTO_VERAPDF=/absolute/path/to/verapdf \
  quarto run publishing/longform.ts build
```

The build then fails unless the one-up PDF passes the configured veraPDF
profile. Routine builds do not require veraPDF. See the
[PDF standards compatibility note](publishing/pdf/standards/README.md) for the
non-tagging KOMA path and the future PDF/UA adoption gate.

## Optional Tools

Regenerate the ignored Zettlr project after changing metadata or chapter
order:

```sh
quarto run publishing/longform.ts zettlr
```

This writes `writing/.ztr-directory`; do not edit or commit it.

Run the integration test and whichever linters are installed:

```sh
python3 publishing/tests/test_build.py
python3 publishing/tests/test_optional_features.py
vale sync
vale writing/manuscript
harper-cli lint -d british -u .harper/dictionary.txt \
  writing/manuscript/*.md writing/manuscript/chapters/*.md
markdownlint-cli2 README.md "docs/**/*.md" "writing/**/*.md" "style/**/*.md"
```

The Harper dictionary is document-owned and should contain only accepted names
or specialist terms from the manuscript. Treat prose-linter findings as
editorial suggestions, especially in quotations and specialist terminology.

## Guides

- [Configure and build](docs/configuration-and-building.md)
- [Use Zettlr](docs/zettlr.md)
- [Customize the project](docs/customization.md)
- [Optional publishing features](publishing/features/README.md)
- [Maintain a tracked downstream](docs/downstream-maintenance.md)
- [Migrate to v0.5](docs/migrating-to-v0.5.md)
