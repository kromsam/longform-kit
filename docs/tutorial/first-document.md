# Build Your First Long-Form Document

## 1. Create The Project

Install Quarto 1.9.38 through 1.9.x and LuaLaTeX. On GitHub, use the **Use this
template** button to create your own copy of the repository, or clone it:

```sh
git clone https://github.com/kromsam/longform-kit YOUR-PROJECT
cd YOUR-PROJECT
bin/longform setup
bin/longform doctor
```

`setup` regenerates the derived adapters (root `index.md` and
`document/.ztr-directory`) from the current configuration; the agent files and
skills already ship in the cloned repository.

## 2. Set Document Metadata

Open `document/metadata.yml` and replace the starter values:

```yaml
book:
  title: "A Reproducible Long-Form Document"
  subtitle: "Writing, Citations, and Output in One Project"
  author: "Your Name"
  date: today
```

The output filename stays in root `_quarto.yml`; set a filename-safe
`book.output-file` there without an extension.

## 3. Write In Zettlr

Open the repository root in Zettlr. The project view lists only the author
Markdown under `document/`. Edit `document/front-matter.md` and replace
`document/manuscript/01-introduction.md` with:

```markdown
# Introduction

{{< epigraph "A document begins by choosing what to foreground." source="Example" >}}

This document uses a reproducible citation [@exampleBook2024, 1-2].

## Research question

How does a document's form shape its argument?
```

The starter bibliography already contains `exampleBook2024`.

## 4. Validate And Render

```sh
bin/longform check
bin/longform build all
```

Open `build/`. You should find:

- `my-document.pdf`
- `my-document-binding.pdf`
- `my-document.docx`
- `my-document.tex`
- `my-document.md`
- `my-document-latex/`

The ordinary PDF has equal margins, while the binding profile has a larger
inner margin. The DOCX uses its native Word TOC and the project reference
document. The GFM output has already expanded Quarto shortcodes and format
conditionals.

## 5. Connect Your References

Configure a Better CSL JSON auto-export to `references/library.json`. Replace
`references/style.csl` only when intentionally choosing another citation style.
Follow [Connect a Zotero collection](../how-to/use-zotero.md) for details.
