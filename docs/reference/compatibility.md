# Compatibility

## Supported In Version 0.1

- Linux and macOS.
- Quarto 1.9.38 through 1.9.x.
- Quarto's bundled Pandoc.
- LuaLaTeX from a current TeX Live or MacTeX installation.
- Long-form books, theses, dissertations, and reports.
- Ordinary PDF, binding PDF, DOCX, LaTeX, and GFM outputs.
- Project-local Better CSL JSON and CSL files.
- Zettlr as an optional authoring interface.
- Vale and Harper as optional prose linters.

`bin/longform doctor` enforces the Quarto and LuaLaTeX requirements. The build
uses Quarto's bundled Pandoc so an unrelated system Pandoc version does not
change canonical rendering.

## Output Notes

PDF, DOCX, and LaTeX are supported combined Quarto book formats. Quarto 1.9 does
not support combined GFM for book projects. Longform Kit therefore resolves the
same ordered inputs with `quarto inspect` and runs `quarto pandoc` directly for
GFM.

Microsoft Word may require field updating when opening a DOCX before its TOC
displays current page numbers.

Fonts named in project configuration must be installed locally and in CI. Font
files are not bundled.

## Deferred

- Windows support.
- HTML, EPUB, and short-article starters.
- Live or write-enabled Zotero connectors.
- Byte-identical outputs across operating systems.

Compatibility changes require a minor release before 1.0 and must be recorded
in `CHANGELOG.md`.
