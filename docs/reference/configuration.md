# Configuration Reference

Edit the public book and build configuration in `quarto/project.yml`. Root
`_quarto.yml` is a minimal regular file that Quarto requires for project
discovery; it loads the substantive configuration and author-owned manuscript
metadata. Configuration paths remain relative to the repository root, and
setup connects the stable citation paths to external Zotero files.

## Project And Book

```yaml
# _quarto.yml
metadata-files:
  - quarto/project.yml
  - document/metadata.yml
  - document/chapters.yml
```

```yaml
# quarto/project.yml
project:
  type: book
  output-dir: build

book:
  output-file: "longform-document"
```

Keep `project.type: book`. The `metadata-files` entries pull the author-owned
manuscript metadata and chapter list in from `document/`; structural build
settings such as `book.output-file` stay in `quarto/project.yml`. The root
loader should change only when the configuration assembly changes.

## Manuscript Metadata

The manuscript's descriptive metadata lives beside the authored content in
`document/metadata.yml` and is merged into the configuration through
`metadata-files`:

```yaml
lang: en-GB

book:
  title: "A Longform Document"
  subtitle: "A Zettlr, Quarto, Pandoc, and Zotero project"
  author: "Author Name"
  date: today
  date-format: "D MMMM YYYY"
```

These are ordinary Quarto keys, so `date: today` resolves to the build date.
Setting them here is equivalent to setting them in `quarto/project.yml`
directly.

## Chapter List

The ordered chapter list lives in `document/chapters.yml`, merged into `book:`
the same way. It is authoritative for every output and for Zettlr
synchronization:

```yaml
book:
  chapters:
    - index.md
    - document/manuscript/01-introduction.md
    - document/references.md
```

`index.md` must remain first and is generated; edit `document/front-matter.md`
instead. Keep `document/references.md` at the intended bibliography position.

## Citations And Structure

```yaml
bibliography: references/library.json
csl: references/style.csl
toc: true
toc-title: Contents
toc-depth: 2
number-sections: true
link-citations: true
```

Longform Kit requires exactly one CSL JSON bibliography. Quarto and its bundled
Pandoc process citations and generate the bibliography natively. The two paths
above are ignored live symlinks created by `bin/longform setup`, not shipped
files. Setup also links `references/zotero-styles` to the active Zotero data
directory's `styles/` folder so it can resolve installed styles by title, CSL
ID, or filename.

The native formats use Quarto's `resource-path` option:

```yaml
resource-path:
  - .
  - references/.csl-parents
  - references/zotero-styles
  - references/zotero-styles/hidden
```

The combined GFM render passes the equivalent Pandoc search path. Retain all
three citation-style directories. Dependent CSL styles need the generated
parent aliases under `references/.csl-parents` or direct access to their
installed independent parent under Zotero's style directories.

Configure a checkout with:

```sh
bin/longform setup \
  --library FILE_OR_DIR \
  --zotero-data-dir DIR \
  --style TITLE_OR_ID_OR_FILENAME
```

`FILE_OR_DIR` is the exact Better CSL JSON export or its containing directory
when the export is named `library.json`. It is separate from the Zotero data
directory and is never `zotero.sqlite`.

Run setup on every machine and in CI. Keep the stable `quarto/project.yml`
paths; do not replace them with personal absolute paths.

## Longform Checks

Only two wrapper-specific settings remain:

```yaml
longform:
  gfm-toc-depth: 2
  required-fonts:
    - EB Garamond
```

`gfm-toc-depth` defaults to the top-level `toc-depth`. `required-fonts` is an
optional list of exact families that `bin/longform doctor` must resolve with
Fontconfig before production rendering.

## Extension And Native Formats

```yaml
shortcodes:
  - quarto/extensions/epigraph/epigraph.lua

format:
  pdf:
    pdf-engine: lualatex
    geometry: "twoside,left=36mm,right=36mm"
    include-in-header:
      - file: quarto/extensions/epigraph/epigraph.tex
  docx:
    toc: true
    reference-doc: references/reference.docx
  latex:
    include-in-header:
      - file: quarto/extensions/epigraph/epigraph.tex
```

The explicit shortcode path registers the vendored extension from its organized
location outside Quarto's conventional root `_extensions/` directory. The
formats are ordinary Quarto names and options. Do not add GFM to this map:
Quarto book projects do not support one combined GFM output, so
`bin/longform build gfm` uses a temporary standalone Quarto render.

`quarto/binding.yml` overrides only binding-specific PDF options. For the
binding build, `bin/longform` selects Quarto's `binding` profile and passes
`--metadata-file=quarto/binding.yml`. Selecting the profile preserves
profile-conditional behavior; the explicit metadata file supplies the
relocated override. Quarto does not auto-discover that file as a root profile,
so bare `quarto render --profile binding` does not apply the binding geometry.
The CLI derives the binding filename from `book.output-file` and appends
`-binding`.
