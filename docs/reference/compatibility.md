# Compatibility

## Supported In Version 0.3

- Linux and macOS.
- Quarto 1.9.38 through 1.9.x and its bundled Pandoc.
- LuaLaTeX from a current TeX Live or MacTeX installation.
- Combined PDF, binding PDF, DOCX, LaTeX, and GFM outputs.
- An external Better CSL JSON export, an installed Zotero CSL style, and a
  project-local DOCX reference file.
- Zettlr as an optional authoring interface.
- Vale and Harper as optional prose linters.

`bin/longform doctor` enforces the Quarto and LuaLaTeX requirements. PDF builds
default `TEXMFCACHE` and `TEXMFVAR` to ignored `.cache/texmf/` only when callers
have not already supplied them, which supports restricted agent sandboxes
without overriding valid TeX configurations.

Every local or CI checkout must run `bin/longform setup` to create its ignored
links to the external citation files. Zotero need not be running during a
build, but the linked Better CSL JSON export and installed style must remain
available at their configured paths.

## Output Notes

PDF, DOCX, and LaTeX are standard combined Quarto book formats. Quarto owns
their TOCs, citations, page breaks, and output writers. Microsoft Word may need
to refresh its native TOC field when opening a DOCX.

Quarto 1.9 does not provide GFM as a combined book format. Longform Kit creates
a temporary standalone Quarto document in the resolved source order and renders
it to GFM. This preserves Quarto shortcodes and `when-format="gfm"`
conditionals without maintaining a parallel Lua transformation pipeline.
Project-relative includes resolve through a temporary resource mirror, and
Pandoc copies embedded figures to `<output-name>_files/` beside the GFM file.
Ordinary links to attachments keep their project-root targets; publish them in
the same repository, or copy those attachments separately when distributing
the GFM outside the project.

Fonts are not bundled. Add production families to
`longform.required-fonts` in `quarto/project.yml` when `doctor` should reject
missing fonts or silent substitution.

## Migration Boundary

Version 0.3 intentionally removes the 0.2 custom project type, custom format
names, semantic epigraph/page-break Divs, manual Word TOC controls, manual
citeproc ordering, and LaTeX-derived GFM compatibility mode. Projects requiring
exact frozen-output parity should keep those rules in a project-owned
compatibility profile rather than in the generic kit.

## Deferred

- Windows support.
- HTML, EPUB, and short-article starters.
- Live or write-enabled Zotero connectors.
- Byte-identical outputs across operating systems.
