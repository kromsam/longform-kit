# AGENTS.md

This repository is a long-form writing project, not an application. Source text
is organized and rendered by Quarto, converted by Pandoc, and cited from a
user-local Zotero/Better BibTeX export. Zettlr is an optional authoring tool.

## Source Of Truth

- Edit title, subtitle, author, date, language, and output filename in
  `writing/manuscript/metadata.yml`; edit chapter order in
  `writing/manuscript/chapters.yml`.
- Edit shared project, PDF, and DOCX defaults in root `_quarto.yml`; put
  committed document-specific rendering overrides and optional-feature
  activation in `_quarto-custom.yml`.
- Keep the rendered manuscript under `writing/manuscript/`. Use
  `writing/drafts/`, `writing/notes/`, and `writing/planning/` for other
  author-owned writing material.
- Treat `style/editorial.md` and `style/typography.md` as document-owned policy.
  Downstreams should customize them; implement rendering changes in Quarto
  configuration or `publishing/`, not by placing executable files in `style/`.
- Do not edit root `index.md`; it is Quarto's adapter for the author-owned front
  matter.
- Treat `_quarto.yml.local` as ignored, user-local configuration. It contains
  absolute `bibliography` and `csl` paths and must never be committed.
- Change bibliographic metadata in Zotero, then let the Better CSL JSON
  auto-export update. Never edit that generated JSON by hand.
- Treat `.harper/dictionary.txt` as document-owned vocabulary. It starts empty;
  do not add terminology from Longform Kit's own documentation or tooling.
- Never edit `output/`, `.cache/`, `.quarto/`, or rendered artefacts.
- `writing/.ztr-directory` is optional generated state. Regenerate it with
  `quarto run publishing/longform.ts zettlr`; do not edit or commit it.

## Working Rules

- Read `style/editorial.md` before changing prose and `style/typography.md`
  before changing presentation policy.
- Preserve citation keys, quotations, factual claims, headings, shortcodes,
  conditional Divs, and authorial meaning during editorial work.
- Do not guess citation details. Verify uncertain metadata in Zotero or through
  an available read-only connector, then update Zotero rather than the export.
- Use `quarto run publishing/longform.ts build` for production builds. Plain
  `quarto render` does not create the complete output set.
- Do not commit absolute home-directory paths or modify a user's global Zettlr
  profile.
- Keep figures and attachments under `materials/`, outside the rendered
  manuscript, and use Quarto project-root paths such as `/materials/figure.png`
  so combined GFM can extract them.
- Keep routine builds offline and provider-independent.
- Apply Harper only to sources under `writing/manuscript/`, as shown in the
  verification command below.
- Treat project scripts, workflows, Quarto extensions, and Agent Skills as
  executable code. Inspect untrusted changes before running them.
- Treat core files outside `publishing/features/` and each explicitly listed
  bundled feature directory as Longform Kit infrastructure. Record ownership
  separately for every downstream-added feature directory; never infer it from
  the parent directory.

## Verification

Before building, create local `_quarto.yml.local` with absolute paths to the
Better CSL JSON export and chosen CSL style:

```yaml
bibliography: /absolute/path/to/library.json
csl: /absolute/path/to/style.csl
```

After changing chapter order, run:

```sh
quarto run publishing/longform.ts zettlr
```

After build or configuration changes, run:

```sh
python3 publishing/tests/test_build.py
python3 publishing/tests/test_optional_features.py
quarto run publishing/longform.ts build
```

This must produce non-empty PDF, two-up PDF, DOCX, and combined GFM files under
`output/`. No LaTeX output is part of the public build.

After prose changes, run whichever configured linters are installed:

```sh
vale writing/manuscript
harper-cli lint -d british -u .harper/dictionary.txt \
  writing/manuscript/*.md writing/manuscript/chapters/*.md
markdownlint-cli2 README.md "docs/**/*.md" "style/**/*.md" \
  "writing/**/*.md"
```

## Agent Skills

Reusable procedures live under `.agents/skills/`. Load the relevant skill
before building, checking citations, linting prose, or performing a clarity
revision.
