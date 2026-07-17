# Use Zettlr

Zettlr is the authoring interface. The canonical build remains
`bin/longform`, so terminals, CI, and AI agents use the same process.

## Open The Project

Open `document/` in Zettlr as the project. `document/.ztr-directory` lists the
resolved author sources — `front-matter.md` in place of Quarto's generated root
`index.md` adapter.

After changing the chapter list in `document/chapters.yml`, run:

```sh
bin/longform zettlr sync
```

Do not change `.ztr-directory` directly.

## Load The Citation Library

Longform Kit links Quarto to a Better CSL JSON export, but it does not change
Zettlr's global preferences. Open **Preferences > Citations** in Zettlr and
select the actual export file resolved by `bin/longform setup`. If
`--library` named a directory, select its `library.json` rather than the
directory.

Zettlr then watches the export for Better BibTeX updates. See the [Zettlr
reference-manager guide](https://docs.zettlr.com/en/guides/reference-manager-integration/)
for the illustrated workflow.

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
