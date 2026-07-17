# Use Zettlr

Zettlr is optional. Quarto configuration and the Markdown sources remain the
source of truth whether or not Zettlr is installed.

## Generate The Project File

From the repository root, run:

```sh
quarto run scripts/longform.ts zettlr
```

The command reads the effective Quarto metadata, replaces root `index.md` with
the author-owned `document/front-matter.md`, and writes
`document/.ztr-directory` with the current title, chapter order, and CSL style.
The generated file is ignored by Git and is not a standard part of the
repository.

Run the command again after changing `document/chapters.yml`, manuscript
metadata, or the local CSL path. Do not edit `.ztr-directory` directly.

## Open And Cite

Open the `document/` directory as the Zettlr project. In **Preferences >
Citations**, select the same Better CSL JSON export named by `bibliography` in
`_quarto.yml.local`. Zettlr's citation-library setting is global, so Longform
Kit does not change it for you.

Use Better BibTeX keys in Markdown:

```markdown
A source can support a specific claim [@authorTitle2026, 44-46].
Several accounts disagree [@firstKey; @secondKey].
```

Change bibliographic metadata in Zotero and let Better BibTeX update the JSON
export. Do not edit the export by hand.

## Export

Use Zettlr for writing and navigation, but use the repository build command for
deliverables:

```sh
quarto run scripts/longform.ts build
```

There is no installed launcher, global Pandoc profile, or Zettlr-specific build
script. This keeps terminal, CI, editor, and agent builds identical.
