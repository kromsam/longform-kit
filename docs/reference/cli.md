# Command-Line Reference

Run commands from the repository root as `bin/longform COMMAND`. Every command
returns a non-zero status on a detected failure.

## `setup`

```sh
bin/longform setup
bin/longform setup \
  --library FILE_OR_DIR \
  --zotero-data-dir DIR \
  --style TITLE_OR_ID_OR_FILENAME
```

On the first run, invoking setup without options prompts for the Better CSL JSON
export location, the active Zotero data directory, and an installed style title,
CSL ID, or filename. `FILE_OR_DIR` may be the exact export file or a directory
containing that export as `library.json`. It is a Better BibTeX export location,
not the Zotero data directory or `zotero.sqlite`.

Style matching reads the installed CSL metadata; it does not derive a filename
from a display title. For a dependent style, setup also requires its independent
parent to be installed.

Setup creates or refreshes these ignored live links:

```text
references/library.json
references/style.csl
references/zotero-styles
references/.csl-parents/ (when a dependent style needs a parent alias)
```

It then restores the exact root `index.md` adapter and synchronizes
`document/.ztr-directory`. Rerunning setup without options revalidates and
reuses the current links. Use all three options for unattended setup in CI.
Every checkout must run setup because citation files and links do not ship in
the repository. The agent files, ignore rules, and Agent Skills do ship, so
setup does not recreate them.

Setup calls are serialized. Do not run setup concurrently with `check` or
`build`: those commands expect the citation links to remain unchanged for their
duration.

## `build`

```sh
bin/longform build [all|pdf|docx|latex|gfm]
```

Every build runs `check` first.

| Target | Outputs |
| --- | --- |
| `all` | All outputs below |
| `pdf` | Ordinary and binding PDFs |
| `docx` | Word document |
| `latex` | Promoted `.tex` plus the complete LaTeX bundle |
| `gfm` | One combined GitHub-flavoured Markdown file |

PDF, DOCX, and LaTeX invoke Quarto's native formats. The wrapper stages them and
promotes stable filenames into `build/`. For the binding PDF it selects the
`binding` profile and explicitly supplies `quarto/binding.yml` as a metadata
file, then appends `-binding` without duplicating the document basename in
configuration. This explicit loading is why `bin/longform` is the supported
interface for binding builds; bare `quarto render --profile binding` does not
discover the relocated override.

GFM creates a temporary standalone Quarto document outside the book project,
mirrors project resources, copies in the pinned epigraph extension from
`quarto/extensions/epigraph/`, and renders with Quarto. This expands includes,
shortcodes, citations, page breaks, and
format conditionals before the result is copied to `build/`. Embedded images
are extracted to `<output-name>_files/` beside the combined Markdown file.
Ordinary attachment links retain their Quarto project-root paths and therefore
expect the GFM to remain in its repository context.

For PDF builds only, unset `TEXMFCACHE` and `TEXMFVAR` default to
`.cache/texmf/`. Existing values, including colon-separated TeX search lists,
are preserved.

## `check`

```sh
bin/longform check
```

Validates:

- Root `index.md` and `document/.ztr-directory` generated state.
- The root Quarto loader, substantive `quarto/project.yml` configuration, and
  resolved source paths.
- The rule that `document/` contains only author-maintained `.md` files plus
  the manuscript metadata in `document/metadata.yml`, the chapter list in
  `document/chapters.yml`, and the generated `document/.ztr-directory` adapter.
- The selected configured CSL file and exactly one linked CSL JSON
  bibliography.
- Non-empty, unique bibliography item IDs and resolution of every cited ID.
- GFM TOC depth and optional required-font configuration.

## `lint`

Runs Vale over `document/**/*.md` and Harper over manuscript Markdown when the
tools are available. If neither is installed, it reports that linting was
skipped and exits successfully.

## `doctor`

Requires Quarto 1.9.38 through 1.9.x and `lualatex`. It reports the bundled
Pandoc version and optional Zettlr availability. When
`longform.required-fonts` is non-empty, it uses Fontconfig's `fc-match` and
rejects missing families or substitutions. Configure that list in
`quarto/project.yml`.

Set `QUARTO` or `LONGFORM_QUARTO` to select a Quarto executable.

## `zettlr`

```sh
bin/longform zettlr sync
bin/longform zettlr install
```

`sync` restores root `index.md` and regenerates `document/.ztr-directory` from
the resolved chapter order. `install` copies a launcher to
`~/.local/bin/longform-zettlr` and prints the custom command to register in
Zettlr.
