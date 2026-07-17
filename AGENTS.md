# AGENTS.md

This repository is a long-form writing project, not an application. Source text
is authored in Zettlr, organized and rendered by Quarto, converted by Pandoc,
and cited from a user-local Zotero/Better BibTeX export linked during setup.

## Source Of Truth

- Edit manuscript metadata (title, subtitle, author, date, language) in
  `document/metadata.yml` and the chapter order in `document/chapters.yml`; edit
  formats and build settings in root `_quarto.yml`.
- Under `document/`, keep only author-owned content: Markdown prose (front
  matter in `document/front-matter.md`, chapters in `document/manuscript/`, the
  bibliography target in `document/references.md`), the manuscript metadata in
  `document/metadata.yml`, and the chapter list in `document/chapters.yml`.
- Do not edit root `index.md`; it is Quarto's adapter for the author-owned front
  matter file.
- Treat `references/library.json`, `references/style.csl`,
  `references/zotero-styles`, and `references/.csl-parents` as ignored,
  user-local setup state created by `bin/longform setup`. Do not edit, copy, or
  commit their targets.
- Change bibliographic metadata in Zotero, then let the configured Better CSL
  JSON auto-export update. Its setup location is either the exact export file
  or a directory containing `library.json`, never the Zotero data directory or
  `zotero.sqlite`. Install and update citation styles through Zotero's Style
  Manager.
- Never edit `build/`, `.cache/`, `.quarto/`, or rendered artefacts.
- `document/.ztr-directory` is generated from `_quarto.yml`; regenerate it with
  `bin/longform zettlr sync`.

## Working Rules

- Read any project editorial style guide before changing prose.
- Preserve citation keys, quotations, factual claims, headings, shortcodes,
  conditional Divs, and authorial meaning during editorial work.
- Do not guess citation details. Verify uncertain metadata in Zotero or through
  an available read-only connector, then update Zotero rather than the linked
  JSON export.
- Use `bin/longform` instead of reconstructing Quarto or Pandoc commands.
- Do not commit absolute home-directory paths or global Zettlr profiles. Local
  citation paths belong only in the ignored setup symlinks.
- Keep figures and attachments outside `document/` and use Quarto project-root
  paths such as `/resources/figure.png` so combined GFM can extract them.
- Keep routine builds offline and provider-independent.
- Treat vendored Quarto extensions, project scripts, workflows, and Agent
  Skills as executable code. Inspect untrusted changes before running them.

## Verification

After cloning, configure the local Zotero inputs before building:

```sh
bin/longform setup --library FILE_OR_DIR --zotero-data-dir DIR --style STYLE
```

After changing chapter order or configuration, run:

```sh
bin/longform zettlr sync
bin/longform check
```

After prose-only changes, run `bin/longform lint` when Vale or Harper is
available. After build changes, run the affected target or
`bin/longform build all`.

PDF, DOCX, and LaTeX are native combined Quarto book renders. GFM is the only
special case: Quarto renders a temporary standalone document so it can expand
shortcodes and conditional content before producing one combined Markdown file.

## Agent Skills

Reusable procedures live under `.agents/skills/`. Load the relevant skill
before building, checking citations, linting prose, or performing a clarity
revision.
