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
  The default body is approximately 15.25/19.3 pt. Use genuine semibold for
  the three heading levels: 27.5/31.5 pt, 20.7/24 pt, and 17.3/20.5 pt.
- Use French spacing, EB Garamond-aware microtype protrusion and controlled
  expansion, three-letter hyphen minima, and 1.5 em of emergency stretch.
- Set notes at 12.7/16 pt, with full-size hanging labels, no separator rule,
  normal note splitting, and numbering restarted at each top-level division.
  Indent body paragraphs and keep at least two lines together at page
  boundaries.
- Target PDF/A-4f for the one-up publication PDF through the dedicated,
  non-tagging PDF-management path. Do not claim PDF/UA while KOMA-Script and
  `tocbasic` remain incompatible with the tagging layer.
- Treat the mirrored-margin PDF as the paginated source of truth. Derive the
  two-up edition from it with a leading blank slot so rectos appear on the
  right without changing page parity. The imposed derivative makes no PDF/A
  or PDF/UA claim.

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
