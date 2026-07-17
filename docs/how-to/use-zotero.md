# Connect A Zotero Collection

Longform Kit reads a live Better CSL JSON export and an installed Zotero CSL
style. Neither file is stored in the repository.

## Export The Library

1. Install Zotero and Better BibTeX.
2. Create or select the collection for the document.
3. Export it with the **Better CSL JSON** translator.
4. Save it outside the project at a stable location.
5. Enable **Keep updated**.

Better BibTeX rewrites this file when the Zotero data changes. The [Zettlr
reference-manager guide](https://docs.zettlr.com/en/guides/reference-manager-integration/)
illustrates the same export workflow.

Setup can receive the exact export file, whatever its filename, or a directory
whose `library.json` is that export. This directory is a Better BibTeX export
location. It is not Zotero's data directory, and `zotero.sqlite` is not an
export file.

## Install The Citation Style

Install the required style through Zotero's **Cite** settings. Zotero can find
styles in its repository or install a local `.csl` file; see [Zotero's citation
style guide](https://www.zotero.org/support/styles).

Next, locate the active Zotero data directory with **Show Data Directory** in
Zotero's advanced settings. This directory contains the `styles/` folder used
by setup. [Zotero's data-directory
documentation](https://www.zotero.org/support/zotero_data) explains the current
platform locations and recommends using that button rather than guessing a
path.

## Link The Project

Run:

```sh
bin/longform setup
```

Provide:

- The exact Better CSL JSON export file, or a directory containing that export
  as `library.json`.
- The active Zotero data directory.
- The installed style's title, CSL ID, or filename.

For unattended setup, including CI, provide all three explicitly:

```sh
bin/longform setup \
  --library FILE_OR_DIR \
  --zotero-data-dir DIR \
  --style TITLE_OR_ID_OR_FILENAME
```

Rerunning setup without options revalidates and reuses the current links.
Style matching reads the metadata of installed CSL files; setup does not guess
a filename by modifying a display title.

Setup resolves the style and creates ignored live links:

```text
references/library.json   -> the Better CSL JSON export
references/style.csl      -> the selected installed style
references/zotero-styles  -> the Zotero data directory's styles/
references/.csl-parents/  -> parent aliases for dependent styles, when needed
```

The stable paths let Quarto, Pandoc, and Zettlr's project adapter use ordinary
project-relative configuration. Because the targets remain external, Better
BibTeX and Zotero style updates are visible on the next check or build.

Run setup in every checkout, including CI. A clone does not contain the
bibliography, citation style, or machine-specific links.

Do not run setup concurrently with `check` or `build`. Setup calls are
serialized, but a check or build expects the citation links to remain unchanged
until it finishes.

## Point Zettlr At The Same Export

Longform Kit does not change Zettlr's global citation preferences. In Zettlr,
open **Preferences > Citations** and select the resolved Better CSL JSON export
file. If setup received a directory, select its `library.json`. Zettlr watches
that file for Better BibTeX updates, as described in its [reference-manager
guide](https://docs.zettlr.com/en/guides/reference-manager-integration/).

## Cite And Check

Use Better BibTeX keys in author Markdown:

```markdown
A single source can anchor a specific claim [@authorTitle2026, 44-46].
Several accounts disagree [@firstKey; @secondKey].
```

Run `bin/longform check`. It fails for missing links, malformed CSL JSON,
duplicate item IDs, or cited keys absent from the export. Correct metadata in
Zotero and let Better BibTeX refresh the linked file; never repair generated
CSL JSON by hand.

The live files are not Git-pinned. Builds can change when Zotero, Better
BibTeX, the export, or an installed style changes, even when the repository has
no diff.
