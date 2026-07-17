# Migrate An Existing Pandoc Or Longform Kit Project

Migrate sources and behaviour separately. Do not copy generated outputs into
the active source tree.

## 1. Inventory The Existing Project

Record ordered Markdown inputs, metadata, bibliography and CSL paths, format
settings, reference DOCX files, fonts, epigraphs, page breaks, TOC expectations,
and representative accepted outputs.

## 2. Establish The Root Quarto Project

Use standard configuration:

```yaml
project:
  type: book
  output-dir: build

format:
  pdf: default
  docx:
    toc: true
    reference-doc: references/reference.docx
  latex: default
```

Move all author-maintained Markdown under `document/`. Put the preface in
`document/front-matter.md`, chapters in `document/manuscript/`, and the
bibliography target in `document/references.md`. Keep `_quarto.yml`, profiles,
references, extensions, scripts, and outputs at the root.

Run `bin/longform setup`; it creates the root `index.md` adapter and Zettlr
project file.

## 3. Localize Citations

Export the Zotero collection as Better CSL JSON to `references/library.json`,
copy the exact CSL to `references/style.csl`, and remove absolute personal
paths. Leave citeproc enabled so Quarto owns citation processing.

## 4. Replace Custom Semantics

Convert legacy epigraph Divs:

```markdown
{{< epigraph "Quotation text." source="Attribution" >}}
```

Convert `.pagebreak` Divs or raw `\newpage` commands:

```markdown
{{< pagebreak >}}
```

Keep Quarto `content-visible` and `content-hidden` Divs. The temporary GFM
render resolves them natively.

## 5. Separate Compatibility From The Generic Kit

Version 0.3 does not carry 0.2's custom title page, front-epigraph placement,
Word TOC switches and blank paragraphs, attached-note punctuation handling, or
LaTeX-derived GFM mode. First test Quarto's native behaviour. If an accepted
frozen export genuinely requires an old rule, keep it in a clearly named,
project-owned compatibility profile or filter rather than restoring it to the
generic Longform Kit.

## 6. Validate And Compare

```sh
bin/longform zettlr sync
bin/longform check
bin/longform build all
```

Compare heading hierarchy, citations, notes, title/TOC/chapter order, page
geometry, typography, DOCX styles, epigraphs, page breaks, and bibliography.
Require structural and visual equivalence where needed, not container hashes.
