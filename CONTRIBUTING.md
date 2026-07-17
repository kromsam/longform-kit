# Contributing

Longform Kit keeps its public behaviour small: a standard Quarto book, a pinned
epigraph shortcode, a Markdown-only authoring directory, and `bin/longform`.

## Development Setup

Install Quarto 1.9.38 through 1.9.x and a TeX distribution containing
LuaLaTeX. Clone the repository, then run:

```sh
bin/longform setup
bin/longform doctor
tests/run.sh
```

Optional prose checks use Vale and Harper when they are on `PATH`.

## Change Guidelines

- Preserve root `_quarto.yml` as the consumer-facing manifest.
- Keep every file under `document/` as author-maintained `.md`.
- Keep builds offline and independent of Zotero, Zettlr, or an AI provider.
- Prefer native Quarto configuration and syntax over new filters or wrappers.
- Do not edit generated files in `build/`, `.cache/`, `.quarto/`, or
  `.ztr-directory`.
- Keep Fancy Epigraphs pinned under `_extensions/epigraph/`; inspect
  upstream changes before upgrading it.
- Treat PDF, DOCX, LaTeX, and GFM behaviour as one public compatibility surface.
- Update documentation, tests, `VERSION`, and `CHANGELOG.md` when the public
  contract changes.

Run the Agent Skills validator after changing a skill:

```sh
for skill in share/templates/skills/*; do
  python /path/to/skill-creator/scripts/quick_validate.py "$skill"
done
```

The validator path depends on the local agent installation. A skill must still
work for agents that only understand the open `SKILL.md` convention.

## Pull Requests

Describe the author-facing behaviour, affected formats, verification commands,
and any visual comparison needed for PDF or DOCX. Do not include credentials,
personal Zotero libraries, submitted manuscripts, or routine build artefacts.
