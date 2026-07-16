# Contributing

Longform Kit keeps its public behavior small: a Quarto project type, a vendored
extension, semantic Markdown conventions, and `bin/longform`.

## Development Setup

Install Quarto 1.9.38 through 1.9.x and a TeX distribution containing
LuaLaTeX. Clone the repository, then run:

```sh
bin/longform setup
bin/longform doctor
bin/longform check
bin/longform build all
```

Optional prose checks use Vale and Harper when they are on `PATH`:

```sh
bin/longform lint
```

## Change Guidelines

- Preserve `document/_quarto.yml` as the consumer-facing manifest.
- Keep builds offline and independent of Zotero, Zettlr, or an AI provider.
- Put portable document semantics in Markdown and Lua filters, not raw
  output-specific source.
- Do not edit generated files in `document/build/`, `document/.quarto/`, or
  `document/.ztr-directory`.
- Keep the extension under `document/_extensions/longform-kit/` so Quarto can
  discover the nested project type.
- Treat PDF, DOCX, LaTeX, and GFM behavior as one public compatibility surface.
- Update documentation and `CHANGELOG.md` when commands, configuration, source
  conventions, or output behavior changes.

Run the Agent Skills validator after changing a skill:

```sh
for skill in share/templates/skills/*; do
  python /path/to/skill-creator/scripts/quick_validate.py "$skill"
done
```

The validator path depends on the local agent installation. A skill must still
work for agents that only understand the open `SKILL.md` convention.

## Pull Requests

Keep changes focused and describe:

1. The author-facing behavior that changes.
2. The formats affected.
3. The commands used to verify the change.
4. Any visual or structural comparison required for PDF or DOCX.

Do not include personal Zotero libraries, credentials, submitted manuscripts,
or generated build artefacts in a pull request.
