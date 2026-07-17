# Use Zettlr

Zettlr is the authoring interface. The canonical build remains
`bin/longform`, so terminals, CI, and AI agents use the same process.

## Open The Project

Open the repository root in Zettlr. Root `.ztr-directory` lists the resolved
author sources under `document/`, including `document/front-matter.md` in place
of Quarto's generated `index.md` adapter.

After changing the chapter list in `document/chapters.yml`, run:

```sh
bin/longform zettlr sync
```

Do not change `.ztr-directory` directly.

## Install The Export Launcher

```sh
bin/longform zettlr install
```

Ensure `~/.local/bin/` is on `PATH`, then register:

```text
longform-zettlr
```

Do not add `$1`; Zettlr appends the selected absolute source paths to the
command automatically.

The launcher finds the project above the active input and runs
`bin/longform build all`. It does not change Zettlr configuration or install
global Pandoc profiles. From Zettlr's integrated terminal, use the same root
command:

```sh
bin/longform build all
```
