# Migrate An Existing Pandoc Or Longform Kit Project

Migrate sources and behaviour separately. Do not copy generated outputs into
the active source tree.

## 1. Inventory The Existing Project

Record ordered Markdown inputs, metadata, bibliography and CSL paths, format
settings, reference DOCX files, fonts, epigraphs, page breaks, TOC expectations,
and representative accepted outputs.

## 2. Establish The Quarto Project Layout

Keep the project-discovery loader at root:

```yaml
# _quarto.yml
metadata-files:
  - quarto/project.yml
  - document/metadata.yml
  - document/chapters.yml
```

Put the substantive standard configuration in `quarto/project.yml`:

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
bibliography target in `document/references.md`. Put the manuscript's
descriptive metadata (title, subtitle, author, date, language) in
`document/metadata.yml` and the ordered chapter list in `document/chapters.yml`,
then let the root loader merge both alongside `quarto/project.yml`.

Keep only Quarto's required `_quarto.yml` loader and `index.md` adapter at the
root. Put binding overrides in `quarto/binding.yml` and vendored extensions
under `quarto/extensions/`; keep references, scripts, and outputs in their
dedicated root directories. Use `bin/longform` to render so the relocated
binding override is applied correctly.

## 3. Connect Citations

Export the Zotero collection as Better CSL JSON to a stable location outside
the repository and enable **Keep updated**. Install the required style in
Zotero, then locate the active Zotero data directory. Run setup and provide the
exact export file or a directory containing it as `library.json`, the Zotero
data directory, and an installed style title, CSL ID, or filename. The export
directory is separate from the Zotero data directory and is not
`zotero.sqlite`. Setup creates ignored live links under `references/`; leave
citeproc enabled so Quarto owns citation processing. It also creates the root
`index.md` adapter and generates the Zettlr project file.

In Zettlr's citation preferences, select the resolved Better CSL JSON export
file. See [Connect a Zotero collection](use-zotero.md) for details.

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
