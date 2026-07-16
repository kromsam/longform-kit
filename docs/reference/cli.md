# Command-Line Reference

Run commands from the repository root as `bin/longform COMMAND`. Every command
returns a non-zero status on a detected failure.

## `setup`

```sh
bin/longform setup
```

Creates `AGENTS.md`, `.gitignore`, and `.agents/skills/` from bundled templates
only when they do not already exist, then synchronizes the Zettlr project file.

## `build`

```sh
bin/longform build [all|pdf|docx|latex|gfm]
```

Runs `check` before rendering.

| Target | Outputs |
| --- | --- |
| `all` | All outputs below |
| `pdf` | Ordinary and binding PDFs |
| `docx` | Word document |
| `latex` | Promoted `.tex` plus LaTeX bundle directory |
| `gfm` | Combined GitHub-flavoured Markdown from the configured GFM source |

Quarto renders each native target in a temporary staging directory before the
wrapper promotes the expected file into `document/build/`. Quarto books do not
support combined GFM, so the wrapper invokes `quarto pandoc` itself. With the
default `longform.gfm-source: markdown`, it reads the chapter order from
`quarto inspect` and applies the project filters, citation data, and metadata.
With `gfm-source: latex`, it first refreshes the canonical LaTeX output and then
converts that file. The LaTeX path requires `link-citations: false` and is
intended for migration or frozen-export parity.

## `check`

```sh
bin/longform check
```

Validates:

- Quarto project configuration and resolved source paths.
- A project-local CSL file and exactly one CSL JSON bibliography.
- Current `document/.ztr-directory` content.
- Non-empty, unique bibliography item IDs.
- Resolution of every cited ID.
- Supported epigraph and page-break structure.

## `lint`

```sh
bin/longform lint
```

Runs Vale over Markdown and Quarto Markdown files when `vale` is available and
Harper over manuscript Markdown when `harper-cli` is available. If neither is
installed, the command reports that linting was skipped and exits successfully.

## `doctor`

```sh
bin/longform doctor
```

Requires Quarto 1.9.38 through 1.9.x and `lualatex`. Reports the bundled Pandoc
version and whether optional Zettlr is available. When
`longform.required-fonts` contains font families, it also requires Fontconfig's
`fc-match` and rejects missing families or silent substitutions.

Set `QUARTO` or `LONGFORM_QUARTO` to select a Quarto executable:

```sh
QUARTO=/opt/quarto/bin/quarto bin/longform doctor
```

## `zettlr`

```sh
bin/longform zettlr sync
bin/longform zettlr install
```

`sync` regenerates `document/.ztr-directory` from Quarto's resolved chapter
order. `install` copies a small launcher to `~/.local/bin/longform-zettlr` and
prints the custom export command to register in Zettlr.
