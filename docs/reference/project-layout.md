# Project Layout

```text
AGENTS.md                         generated consumer instructions
.agents/skills/                   generated provider-neutral Agent Skills
bin/longform                      stable command-line interface
document/                         Zettlr and Quarto project root
  _quarto.yml                     sole project manifest
  _quarto-binding.yml             binding PDF overrides
  .ztr-directory                  generated Zettlr project adapter
  index.qmd                       required book entry and front matter
  manuscript/*.md                 active chapters
  references.md                   bibliography heading and Div#refs
  references/
    library.json                  Better CSL JSON auto-export
    style.csl                     pinned citation style
  _extensions/longform-kit/       vendored executable Quarto extension
  build/                          ignored generated outputs
share/templates/                  files materialized by setup
style/                            optional project editorial guidance
submissions/                      optional frozen deliverables
```

The nested `document/` directory is both the Zettlr workspace and the Quarto
project root. Quarto discovers custom project types only from an `_extensions`
directory at that root, which is why the vendored extension lives inside
`document/`.

`index.qmd` must keep that name because Quarto books require it. Other prose may
use `.md` or `.qmd`; ordinary chapters use `.md` by convention.

`document/.ztr-directory`, `document/.quarto/`, and `document/build/` are
generated. Only `.ztr-directory` is normally committed, so a fresh Zettlr
checkout has the ordered project immediately available.
