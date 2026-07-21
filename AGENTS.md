# AGENTS.md

This repository is a long-form writing project, not an application. Source text
is organized and rendered by Quarto, converted by Pandoc, and cited from a
user-local Zotero/Better BibTeX export. Zettlr is an optional authoring tool.

## Source Of Truth

- Edit title, subtitle, author, date, language, and output filename in
  `document/metadata.yml`; edit chapter order in `document/chapters.yml`.
- Edit shared project, PDF, and DOCX defaults in root `_quarto.yml`; put
  committed document-specific rendering overrides in `_quarto-custom.yml`.
- Under `document/`, keep only author-owned content: front matter, manuscript
  chapters, the bibliography target, manuscript metadata, and chapter order.
- Do not edit root `index.md`; it is Quarto's adapter for the author-owned front
  matter.
- Treat `_quarto.yml.local` as ignored, user-local configuration. It contains
  absolute `bibliography` and `csl` paths and must never be committed.
- Change bibliographic metadata in Zotero, then let the Better CSL JSON
  auto-export update. Never edit that generated JSON by hand.
- Never edit `build/`, `.cache/`, `.quarto/`, or rendered artefacts.
- `document/.ztr-directory` is optional generated state. Regenerate it with
  `quarto run scripts/longform.ts zettlr`; do not edit or commit it.

## Working Rules

- Read any project editorial style guide before changing prose.
- Preserve citation keys, quotations, factual claims, headings, shortcodes,
  conditional Divs, and authorial meaning during editorial work.
- Do not guess citation details. Verify uncertain metadata in Zotero or through
  an available read-only connector, then update Zotero rather than the export.
- Use `quarto run scripts/longform.ts build` for production builds. Plain
  `quarto render` does not create the complete output set.
- Do not commit absolute home-directory paths or modify a user's global Zettlr
  profile.
- Keep figures and attachments outside `document/` and use Quarto project-root
  paths such as `/resources/figure.png` so combined GFM can extract them.
- Keep routine builds offline and provider-independent.
- Treat project scripts, workflows, Quarto extensions, and Agent Skills as
  executable code. Inspect untrusted changes before running them.

## Verification

Before building, create local `_quarto.yml.local` with absolute paths to the
Better CSL JSON export and chosen CSL style:

```yaml
bibliography: /absolute/path/to/library.json
csl: /absolute/path/to/style.csl
```

After changing chapter order, run:

```sh
quarto run scripts/longform.ts zettlr
```

After build or configuration changes, run:

```sh
quarto run scripts/longform.ts build
```

This must produce non-empty PDF, two-up PDF, DOCX, and combined GFM outputs. No
LaTeX output is part of the public build.

After prose changes, run whichever configured linters are installed:

```sh
vale document
harper-cli lint -d british -u .harper/dictionary.txt document/*.md document/manuscript/*.md
markdownlint-cli2 README.md "docs/**/*.md" "document/**/*.md"
```

## Agent Skills

Reusable procedures live under `.agents/skills/`. Load the relevant skill
before building, checking citations, linting prose, or performing a clarity
revision.
