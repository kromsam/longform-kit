# Configure And Build

Longform Kit keeps shared project settings in Git and machine-specific
citation paths out of Git. There is no setup program and no symlink layer.

## Configure Citations

In Zotero with Better BibTeX installed, export the collection for the document
using **Better CSL JSON** and enable **Keep updated**. Save the export at a
stable location outside the repository. Install or download the CSL style that
the document should use.

Create `_quarto.yml.local` in the project root:

```yaml
bibliography: /home/you/Documents/zotero-exports/project-library.json
csl: /home/you/Zotero/styles/chicago-fullnote-bibliography.csl
```

Use absolute paths. On Windows, forward slashes are the least surprising YAML
form, for example `C:/Users/you/Documents/library.json`. The bibliography must
be a CSL JSON export – not the Zotero data directory and not `zotero.sqlite`.

Dependent CSL styles refer to a separate parent style. Prefer a self-contained
style, or keep the required parent style installed and available beside the
selected style. If Pandoc reports that it cannot resolve a parent style, select
the independent parent or download a self-contained style from the Zotero
style repository.

`_quarto.yml.local` is ignored because it contains personal paths. Configure it
separately on every machine and in CI.

## Edit The Manuscript

Edit descriptive metadata in `document/metadata.yml`:

```yaml
lang: en-GB

book:
  title: "A Longform Document"
  subtitle: "An optional subtitle"
  author: "Author Name"
  date: today
```

Edit the reading order in `document/chapters.yml`:

```yaml
book:
  chapters:
    - index.md
    - document/manuscript/01-introduction.md
    - document/manuscript/02-conclusion.md
    - document/references.md
```

Keep `index.md` first and edit `document/front-matter.md` instead of the root
adapter. Keep `document/references.md` where the generated bibliography should
appear.

Shared Quarto settings live in `_quarto.yml`. `_quarto-binding.yml` changes
only the binding PDF's filename and two-sided layout. The ordinary PDF uses
KOMA's default equal left and right margins while retaining blank verso pages
so every chapter begins on a recto page. The `twoside=semi,openright` class
options combine that symmetric type area with two-sided pagination. The binding
profile keeps the same page sequence but switches to KOMA's default mirrored
margins with `twoside,openright`.

## Build Every Format

Run the canonical build from the project root:

```sh
quarto run scripts/longform.ts build
```

One invocation always creates the complete set:

```text
build/longform-document.pdf
build/longform-document-binding.pdf
build/longform-document.docx
build/longform-document.md
```

The two PDFs and DOCX are native combined Quarto book renders. GFM is the one
special case: the build program resolves the chapter list into a temporary
standalone Quarto document, renders it through Pandoc, extracts referenced
media, and removes the temporary source. This preserves citations, includes,
shortcodes, and `when-format="gfm"` conditionals without keeping a LaTeX
intermediate.

Plain `quarto render` is useful for diagnosis but is not the production build:
it cannot create both PDF layouts and the combined GFM edition in one render.

## Check The Result

The build command fails if a required output is missing or empty. For layout
changes, also inspect both PDFs and the DOCX rather than relying on exit status.
Check that the binding PDF uses KOMA's default mirrored margins. Both PDFs
should retain blank verso pages so chapters begin on recto pages; the ordinary
PDF uses KOMA's default equal margins instead.

Useful diagnostics are:

```sh
quarto check
quarto inspect
```

Do not patch files under `build/`; fix the Markdown, Quarto configuration, CSL
input, or `references/reference.docx` and rebuild.

## Run The Linters

The repository includes independent editor/CLI configuration for three tools.
Install whichever ones suit your workflow.

Vale supplies the tracked `Academic` house style and downloads proselint as a
low-authority advisory layer:

```sh
vale sync
vale document
```

Harper uses British English and the project dictionary at
`.harper/dictionary.txt`:

```sh
harper-cli lint -d british -u .harper/dictionary.txt document/*.md document/manuscript/*.md
```

Add only accepted names and specialist terms to that dictionary. Markdownlint
uses its Prettier-compatible style from the project root:

```sh
markdownlint-cli2 README.md "docs/**/*.md" "document/**/*.md"
```

Linters provide evidence, not editorial authority. Do not rewrite quotations,
citation keys, or deliberate specialist language simply to silence a warning.
