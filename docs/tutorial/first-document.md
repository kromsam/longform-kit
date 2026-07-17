# Build Your First Long-Form Document

## 1. Prepare Zotero

Install Zotero and Better BibTeX. Export the library or collection for this
document with the **Better CSL JSON** translator, save it at a stable location,
and enable **Keep updated**.

Install the citation style you want through Zotero's **Cite** settings. Then use
**Show Data Directory** in Zotero's advanced settings to locate the active data
directory. Keep the export location and data-directory path available for
setup. The export location may be the exact file or, when it is named
`library.json`, its containing directory. That export directory is distinct
from Zotero's data directory and `zotero.sqlite`.

For the complete workflow, see [Connect a Zotero
collection](../how-to/use-zotero.md).

## 2. Create The Project

Install Quarto 1.9.38 through 1.9.x and LuaLaTeX. On GitHub, use the **Use this
template** button to create your own copy of the repository, or clone it:

```sh
git clone https://github.com/kromsam/longform-kit YOUR-PROJECT
cd YOUR-PROJECT
bin/longform setup
bin/longform doctor
```

Setup asks for the Better CSL JSON export file or containing directory, the
Zotero data directory, and an installed style title, CSL ID, or filename. It
creates ignored live links under `references/` and regenerates the root
`index.md` and `document/.ztr-directory` adapters. Run setup in every checkout,
including CI.

In Zettlr, open **Preferences > Citations** and select the resolved Better CSL
JSON export file manually. If setup received a directory, select its
`library.json`.

## 3. Set Document Metadata

Open `document/metadata.yml` and replace the starter values:

```yaml
book:
  title: "A Long-Form Document"
  subtitle: "Writing, Citations, and Output in One Project"
  author: "Your Name"
  date: today
```

The output filename stays in `quarto/project.yml`; set a filename-safe
`book.output-file` there without an extension. Keep root `_quarto.yml` as the
small Quarto project loader.

## 4. Write In Zettlr

Open `document/` in Zettlr as the project. The project view lists only the
author Markdown. Edit `document/front-matter.md` and replace
`document/manuscript/01-introduction.md` with:

```markdown
# Introduction

{{< epigraph "A document begins by choosing what to foreground." source="Example" >}}

This document uses a source from my Zotero library [@yourCitationKey, 1-2].

## Research question

How does a document's form shape its argument?
```

Replace `yourCitationKey` with an actual Better BibTeX key from the linked
export. Zettlr can insert keys after it loads that same export in its citation
preferences.

## 5. Validate And Render

```sh
bin/longform check
bin/longform build all
```

Open `build/`. You should find:

- `longform-document.pdf`
- `longform-document-binding.pdf`
- `longform-document.docx`
- `longform-document.tex`
- `longform-document.md`
- `longform-document-latex/`

The ordinary PDF has equal margins, while the binding build has a larger inner
margin from `quarto/binding.yml`. The DOCX uses its native Word TOC and the
project reference document. The GFM output has already expanded Quarto
shortcodes and format conditionals.

The citation inputs are live rather than Git-pinned. A Better BibTeX refresh or
installed-style update affects the next check and build.
