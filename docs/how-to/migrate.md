# Migrate An Existing Pandoc Project

Migrate source and behavior separately. Do not copy generated outputs into the
new source tree.

## 1. Inventory The Existing Project

Record:

- Ordered Markdown inputs and front matter.
- Shared metadata and output basename.
- Bibliography and CSL sources.
- Pandoc defaults, filters, templates, and reference DOCX files.
- PDF geometry, fonts, title-page rules, epigraphs, page breaks, and TOC order.
- Existing outputs used for visual comparison.

## 2. Move Authoritative Sources

Put front matter in `document/index.qmd`, active chapters in
`document/manuscript/`, and the bibliography location in
`document/references.md`. Add every ordered source to `book.chapters` in
`document/_quarto.yml`.

Keep notes, drafts, archives, and frozen submissions outside the active chapter
list.

## 3. Localize Citations

Create a project collection in Zotero, export it as Better CSL JSON to
`document/references/library.json`, and copy the exact CSL style to
`document/references/style.csl`. Remove absolute paths to a personal Zotero
profile.

## 4. Replace Output-Specific Source

Convert raw epigraphs and page breaks to the semantic forms documented in
[Semantic Markdown](../reference/semantic-markdown.md). Replace format-only raw
content with supported Quarto conditional Divs. Move project-level format
options into `_quarto.yml` or the binding profile.

## 5. Encode Only The Required Compatibility Rules

Keep `longform.gfm-source: markdown` unless comparison shows that the accepted
GFM depends on the canonical LaTeX export. In that case, select `latex` and set
the GFM TOC depth independently:

```yaml
longform:
  gfm-source: latex
  gfm-toc-depth: 2
link-citations: false
```

The LaTeX-derived path requires citation links to be disabled and resolves
format conditionals for LaTeX. Record that tradeoff in the project
documentation.

Translate verified DOCX behavior into explicit options rather than carrying
forward output patches. Available controls include `docx-toc-depth`,
`docx-toc-switches`, `docx-toc-heading-pagebreak`, `docx-toc-leading-blank`,
`docx-bibliography-leading-blank`, and
`preserve-attached-note-positions`. Epigraph Divs can select a leading break,
separator, flush quotation, or named DOCX styles. Leave each compatibility
setting at its default until a structural or visual comparison demonstrates the
need for it.

List production font families under `longform.required-fonts` when substitution
would invalidate the comparison, then run `bin/longform doctor` on every build
machine.

## 6. Validate And Compare

```sh
bin/longform zettlr sync
bin/longform check
bin/longform build all
```

Compare heading hierarchy, citations, notes, title-to-TOC order, bibliography,
page geometry, typography, and DOCX styles with the reference outputs. Require
visual and structural parity, not byte identity.

Only retire old scripts, copied templates, global Zettlr profiles, and tracked
routine exports after parity is established. Preserve intentional submitted
versions in a separate `submissions/` directory.
