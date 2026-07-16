# Build Your First Long-Form Document

This tutorial creates a small cited document and renders every supported output.

## 1. Create The Project

Install Quarto 1.9.38 through 1.9.x and LuaLaTeX, then run:

```sh
quarto use template kromsam/longform-kit
cd YOUR-PROJECT
bin/longform setup
bin/longform doctor
```

`setup` creates the provider-neutral agent files that Quarto starter templates
intentionally omit and generates `document/.ztr-directory`.

## 2. Set Document Metadata

Open `document/_quarto.yml` and replace the starter values:

```yaml
book:
  title: "Material Witnesses"
  subtitle: "A Study in Three Chapters"
  author: "Your Name"
  date: today
  output-file: "material-witnesses"
```

Use a filename-safe `output-file` without an extension. The CLI appends
`-binding` to the binding PDF automatically, so the profile only needs to hold
its layout overrides.

## 3. Write In Zettlr

Open the `document/` directory as a Zettlr project. `index.qmd` holds front
matter, and `manuscript/` holds the chapters.

Replace `document/manuscript/01-introduction.md` with:

```markdown
# Introduction

This document uses a reproducible citation [@exampleBook2024, 1-2].

## Research question

How does a document's form shape its argument?
```

The starter bibliography already contains `exampleBook2024`, so the citation
can be checked without a running Zotero instance.

## 4. Validate The Sources

From the repository root, run:

```sh
bin/longform check
```

The check confirms that the configured source files exist, the CSL and CSL JSON
files are local, the Zettlr project is synchronized, citation IDs resolve, and
semantic blocks are valid.

## 5. Render Every Format

```sh
bin/longform build all
```

Open `document/build/`. You should find:

- `material-witnesses.pdf`
- `material-witnesses-binding.pdf`
- `material-witnesses.docx`
- `material-witnesses.tex`
- `material-witnesses.md`
- `material-witnesses-latex/`

The ordinary PDF has equal margins. The binding copy has a larger inner margin.
The LaTeX directory retains the complete source bundle as well as the promoted
top-level `.tex` file.

## 6. Connect Your Own References

Create a Zotero collection for this document and configure a Better CSL JSON
auto-export to `document/references/library.json`. Replace
`document/references/style.csl` only when you intentionally choose another
citation style. Follow [Connect a Zotero collection](../how-to/use-zotero.md)
for the complete workflow.

You now have one ordered Markdown source rendered reproducibly to all five
canonical artefacts.
