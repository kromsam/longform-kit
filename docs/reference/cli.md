# Command-Line Reference

Run commands from the repository root as `bin/longform COMMAND`. Every command
returns a non-zero status on a detected failure.

## `setup`

```sh
bin/longform setup
```

Creates `AGENTS.md`, `.gitignore`, and `.agents/skills/` from templates only
when they do not exist, and generates a project `LICENSE` from
`share/templates/LICENSE.in` with the year and the `book.author` from
`_quarto.yml` filled in. The kit's own MIT notice is deliberately not carried
into generated projects (see `.quartoignore`); the licence belongs to the
project's author. The command also restores the exact root `index.md` adapter
and synchronizes `.ztr-directory`.

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
promotes stable filenames into `build/`; this lets the binding profile append
`-binding` without duplicating the document basename in configuration.

GFM creates a temporary standalone Quarto document outside the book project,
mirrors project resources, copies in the pinned epigraph extension, and renders
with Quarto. This expands includes, shortcodes, citations, page breaks, and
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

- Root `index.md` and `.ztr-directory` generated state.
- Native Quarto configuration and resolved source paths.
- The rule that `document/` contains only author-maintained `.md` files plus
  the manuscript metadata in `document/metadata.yml` and the chapter list in
  `document/chapters.yml`.
- A project-local CSL file and exactly one CSL JSON bibliography.
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
rejects missing families or substitutions.

Set `QUARTO` or `LONGFORM_QUARTO` to select a Quarto executable.

## `zettlr`

```sh
bin/longform zettlr sync
bin/longform zettlr install
```

`sync` restores root `index.md` and regenerates root `.ztr-directory` from the
resolved chapter order. `install` copies a launcher to
`~/.local/bin/longform-zettlr` and prints the custom command to register in
Zettlr.
