# Use Zettlr

Zettlr is the authoring interface. The canonical build remains
`bin/longform`, so the same process works in a terminal, CI, or an AI-agent
session.

## Open The Project

Open the repository's `document/` directory in Zettlr. The generated
`document/.ztr-directory` contains the source files in the order resolved from
`document/_quarto.yml`.

After changing `book.chapters`, run:

```sh
bin/longform zettlr sync
```

Do not change the order in `.ztr-directory` directly.

## Install The Export Launcher

```sh
bin/longform zettlr install
```

This installs `longform-zettlr` in `~/.local/bin/`. Ensure that directory is on
`PATH`, then register this Zettlr custom export command:

```text
longform-zettlr "$1"
```

The launcher finds the Longform Kit project above the active input file and
runs `bin/longform build all`. It does not modify Zettlr's configuration or
install global Pandoc profiles.

You may also build from Zettlr's integrated terminal:

```sh
../bin/longform build all
```

Zettlr can edit the required `index.qmd` file as Markdown. Quarto, rather than
the file extension, supplies its book role.
