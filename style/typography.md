# Typography

This guide records Longform Kit's starter presentation policy. A downstream
project owns and may replace it. Keep policy here, but implement it in
`_quarto.yml`, `_quarto-custom.yml`, and `publishing/`; executable filters,
templates, and scripts do not belong in `style/`.

## PDF

- Set the book on A4 with a two-sided, open-right KOMA-Script layout.
- Use KOMA's `areaset` for a 140 × 227 mm type area, following Bringhurst's A4
  construction. Preserve any binding correction (`BCOR`) and let KOMA mirror
  the margins; do not add Quarto `geometry` unless deliberately replacing this
  layout model.
- Use EB Garamond with old-style figures for the main, sans, and mono roles.
  The default body is approximately 15.25/19.3 pt.
- Set notes at 11.4/15.25 pt, with full-size hanging labels, no separator rule,
  and normal note splitting. Indent body paragraphs and keep at least two lines
  of a paragraph together at page boundaries.
- Treat the mirrored-margin PDF as the paginated source of truth. Derive the
  two-up edition from it with a leading blank slot so rectos appear on the
  right without changing page parity.

## DOCX and reflowable output

- Control Word presentation through `publishing/docx/reference.docx`. Keep its
  paragraph and character styles semantic and use EB Garamond by default.
- Keep DOCX package sanitizing in `publishing/docx/sanitize.lua`; typography
  policy must not depend on machine-local document metadata.
- Preserve semantic Markdown for DOCX and combined GFM. Prefer portable Quarto
  structures to raw LaTeX whenever material must survive across formats.

When changing this policy, update the corresponding configuration or
publishing asset and inspect both PDFs and the DOCX; a successful build alone
does not verify typography.
