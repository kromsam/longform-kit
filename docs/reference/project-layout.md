# Project Layout

```text
AGENTS.md                         provider-neutral repository instructions
.agents/skills/                   provider-neutral Agent Skills
_quarto.yml                       standard Quarto book manifest
_quarto-binding.yml               binding PDF profile
index.md                          generated Quarto home-page adapter
bin/longform                      stable command-line interface
bin/longform-zettlr               Zettlr custom-export launcher
scripts/project.ts                checks, Zettlr sync, and combined GFM
document/                         author-owned manuscript content
  .ztr-directory                  generated Zettlr project adapter
  metadata.yml                    title, subtitle, author, date, language
  chapters.yml                    ordered chapter list
  front-matter.md                 preface and other opening content
  manuscript/*.md                 active chapters
  references.md                   bibliography heading and Div#refs
references/
  library.json                    ignored link to Better CSL JSON export
  style.csl                       ignored link to selected installed style
  zotero-styles                   ignored link to Zotero's styles/ directory
  .csl-parents/                   ignored aliases for dependent style parents
  reference.docx                 Word style template
resources/                        optional figures and attachments
_extensions/epigraph/             pinned Fancy Epigraphs v0.0.1
build/                            ignored generated outputs
.cache/texmf/                     ignored sandbox-safe TeX cache
style/                            optional editorial guidance
submissions/                      optional frozen deliverables
```

The `resources/`, `style/`, and `submissions/` directories are optional and
author-created: a freshly generated project does not contain them until you add
them.

The Zotero setup entries under `references/` are not shipped. `bin/longform
setup` creates them for each checkout from the exact Better CSL JSON export or
a directory containing it as `library.json`, the active Zotero data directory,
and an installed style title, CSL ID, or filename. The export directory is not
the Zotero data directory or `zotero.sqlite`. The links remain live, so Better
BibTeX export changes and Zotero style updates appear without copying files
into the project. The tracked `reference.docx` is unrelated to Zotero and
remains project-owned.

`document/` is a strict authoring boundary. The only non-Markdown files allowed
below it are `document/metadata.yml` (the manuscript's descriptive metadata),
`document/chapters.yml` (the ordered chapter list), and the generated
`document/.ztr-directory` Zettlr adapter. The two YAML files are merged into
`book:` through `metadata-files` in `_quarto.yml`. `bin/longform check` rejects
every other non-Markdown file there, including the rest of the Quarto
configuration, generated outputs, reference exports, and editor state.

Store figures and attachments in a root directory such as `resources/`. Refer
to them with Quarto project-root paths (`/resources/figure.png`), including from
included Markdown, so native book renders and the combined GFM resource mirror
resolve the same file.

Quarto requires `index.md` for a book. Longform Kit keeps that mechanical file
at the root and has it include `document/front-matter.md`; `setup` and
`zettlr sync` restore the exact adapter. The Zettlr project lists the included
front-matter file rather than the adapter, so authors only navigate files they
own.
