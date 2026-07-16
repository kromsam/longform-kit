# Compatibility

## Supported In Version 0.2

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
not support combined GFM for book projects, so Longform Kit runs
`quarto pandoc` through one of two explicit paths:

- `longform.gfm-source: markdown` is the default. It resolves the ordered
  Markdown inputs with `quarto inspect`, processes citations and the Longform
  Kit filters, and preserves `when-format="gfm"` conditionals.
- `longform.gfm-source: latex` refreshes the canonical LaTeX build and converts
  that output. It is intended for migrations where LaTeX-level epigraphs, page
  breaks, language spans, nested quotation output, or bibliography structure
  define the compatibility baseline.

LaTeX-derived GFM requires `link-citations: false`; the build fails early when
links remain enabled. Citeproc has already rendered the notes and bibliography
into the LaTeX source, and adding links during the second conversion can change
their structure. GFM-specific conditionals are resolved as LaTeX conditionals
in this mode. LaTeX-derived GFM uses YAML metadata so document metadata remains
machine-readable without introducing an extra title heading into the body.
Values that YAML could reinterpret as booleans, numbers, nulls, or dates are
quoted by default. The `gfm-legacy-plain-scalars` switch exists only for
byte-level comparison with an established export and can change parsed
metadata types.

Microsoft Word may require field updating when opening a DOCX before its TOC
displays current page numbers. Longform Kit stores a dirty TOC field and asks
Word to update fields; cached TOC entries and package bytes can therefore differ
between applications even when the document content and layout agree.

DOCX compatibility controls can set an independent TOC depth, insert deliberate
blank paragraphs around the TOC or bibliography, preserve attached citation
note positions, and tune chapter epigraph spacing and styles. These options are
off by default unless their reference entry states otherwise. They reproduce
established layout conventions without making those conventions universal.

Fonts named in project configuration must be installed locally and in CI. Font
files are not bundled. Add production families to `longform.required-fonts` when
`doctor` should reject missing fonts or substitutions before rendering.

## Deferred

- Windows support.
- HTML, EPUB, and short-article starters.
- Live or write-enabled Zotero connectors.
- Byte-identical outputs across operating systems.

Compatibility changes require a minor release before 1.0 and must be recorded
in `CHANGELOG.md`.
