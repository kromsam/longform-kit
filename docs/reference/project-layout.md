# Project Layout

```text
AGENTS.md                         provider-neutral repository instructions
.agents/skills/                   provider-neutral Agent Skills
_quarto.yml                       standard Quarto book manifest
_quarto-binding.yml               binding PDF profile
index.md                          generated Quarto home-page adapter
.ztr-directory                    generated Zettlr project adapter
bin/longform                      stable command-line interface
scripts/project.ts                checks, Zettlr sync, and combined GFM
document/                         author-maintained Markdown only
  front-matter.md                 preface and other opening content
  manuscript/*.md                 active chapters
  references.md                   bibliography heading and Div#refs
references/
  library.json                    Better CSL JSON auto-export
  style.csl                       pinned citation style
  reference.docx                 Word style template
resources/                        optional figures and attachments
_extensions/epigraph/             pinned Fancy Epigraphs v0.0.1
build/                            ignored generated outputs
.cache/texmf/                     ignored sandbox-safe TeX cache
share/templates/                  files materialized by setup
style/                            optional editorial guidance
submissions/                      optional frozen deliverables
```

The `resources/`, `style/`, and `submissions/` directories are optional and
author-created: a freshly generated project does not contain them until you add
them.

`document/` is a strict authoring boundary. `bin/longform check` rejects every
non-Markdown file below it, including Quarto configuration, generated outputs,
reference exports, and editor state.

Store figures and attachments in a root directory such as `resources/`. Refer
to them with Quarto project-root paths (`/resources/figure.png`), including from
included Markdown, so native book renders and the combined GFM resource mirror
resolve the same file.

Quarto requires `index.md` for a book. Longform Kit keeps that mechanical file
at the root and has it include `document/front-matter.md`; `setup` and
`zettlr sync` restore the exact adapter. The Zettlr project lists the included
front-matter file rather than the adapter, so authors only navigate files they
own.
