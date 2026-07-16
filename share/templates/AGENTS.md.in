# AGENTS.md

This repository is a long-form writing project, not an application. Source text
is authored in Zettlr, organized and rendered by Quarto, converted by Pandoc,
and cited from a project-local Zotero/Better BibTeX export.

## Source Of Truth

- Edit document metadata and chapter order only in `document/_quarto.yml`.
- Write front matter in `document/index.qmd` and chapters in
  `document/manuscript/`.
- Keep the bibliography location in `document/references.md` as a `Div#refs`.
- Treat `document/references/library.json` as a generated Better CSL JSON export.
  Change bibliographic metadata in Zotero, then let Better BibTeX update it.
- Keep the exact CSL style in `document/references/style.csl` under version
  control.
- Never edit `document/build/`, `document/.quarto/`, or other rendered artefacts.
- `document/.ztr-directory` is generated from `_quarto.yml`; regenerate it with
  `bin/longform zettlr sync`.

## Working Rules

- Read any project editorial style guide before changing prose.
- Preserve citation keys, quotations, factual claims, headings, semantic Divs,
  and authorial meaning during editorial work.
- Do not guess citation details. Verify uncertain metadata in Zotero or through
  an available read-only connector, then update Zotero rather than its JSON
  export.
- Use `bin/longform` instead of reconstructing Quarto or Pandoc commands.
- Do not introduce absolute home-directory paths or depend on global Zettlr
  export profiles.
- Keep normal builds offline and provider-independent.
- Treat vendored Quarto extensions, Lua filters, project scripts, and Agent
  Skills as executable code. Inspect untrusted changes before running them.

## Verification

After changing chapter order, citations, semantic markup, configuration, or
export behavior, run:

```sh
bin/longform zettlr sync
bin/longform check
```

After prose-only changes, run `bin/longform lint` when Vale or Harper is
available. After build-related changes, run the affected target or
`bin/longform build all`.

The canonical outputs are PDF, binding PDF, DOCX, LaTeX, and GFM. PDF, DOCX,
and LaTeX are Quarto book renders. GFM uses Quarto's bundled Pandoc over the
chapter order resolved by `quarto inspect`, because Quarto books do not support
combined GFM output.

## Agent Skills

Reusable procedures live under `.agents/skills/`. Load the relevant skill before
building, checking citations, linting prose, or performing a clarity revision.
