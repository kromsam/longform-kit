# Customize The Project

Longform Kit separates policy from implementation. Editorial and typographic
decisions belong in `style/`; Quarto configuration, filters, templates, DOCX
assets, and conversion code belong in `publishing/` or the root Quarto profile.

Root `_quarto.yml` contains shared defaults and activates the tracked
`_quarto-custom.yml` profile. Put committed document-specific overrides in
that profile and machine-specific citation paths in ignored
`_quarto.yml.local`.

## Change Output Settings

Add document-specific settings such as table-of-contents depth, section
numbering, binding correction, extra filters, and header includes to
`_quarto-custom.yml`. Edit root `_quarto.yml` only when changing shared
Longform Kit defaults or replacing an inherited list entry.

Keep `book.output-file` beside the title and author in
`writing/manuscript/metadata.yml`. The build uses that name for PDF, DOCX, and
combined Markdown, and appends `-2up` for the imposed PDF.

The defaults leave headings unnumbered and include chapters only in the table
of contents. A document that needs numbered sections or a deeper contents list
can opt in:

```yaml
toc-depth: 2
number-sections: true
```

## Change PDF Typography

Read `style/typography.md` before changing the implementation. The default
type area is set by `\areaset[current]{140mm}{227mm}` in `_quarto.yml`.
`current` preserves the active KOMA binding correction. The project does not
set Quarto's `geometry` option because that would bypass this KOMA type-area
policy.

The non-standard 15.25 pt body size is a keyed KOMA class option. Keep
`fontsize=15.25pt` in the class-option string when changing other options;
Quarto's bare `fontsize` field does not make this arbitrary size effective.
Adjust measure, leading, body size, and footnote hierarchy as a system, then
inspect both PDFs and the DOCX.

The PDF starts with `BCOR=0mm`. Once a printer or binding method supplies the
width of paper physically lost at the spine, override that scalar in
`_quarto-custom.yml`, for example:

```yaml
format:
  pdf:
    classoption: "twoside,openright,BCOR=8mm,fontsize=15.25pt"
```

Do not use `BCOR` merely to request a wider-looking gutter.
`areaset[current]` preserves the replacement correction automatically. A
document may deliberately replace `areaset` with KOMA's divisor construction
or Quarto geometry, but that is a different page-design policy and needs visual
verification.

EB Garamond is assigned to the PDF main, sans, and mono families by default.
Override `format.pdf.monofont` when source code must retain fixed-width
alignment.

## Change DOCX Styles

Edit a copy of `publishing/docx/reference.docx` in Word or LibreOffice and
retain it at that tracked path. Quarto applies its named styles when producing
DOCX. Keep the generic reference document upstream-owned when maintaining a
tracked downstream; reusable style changes should be contributed to Longform
Kit first.

The build runs `publishing/docx/sanitize.lua` after rendering. Do not patch a
generated DOCX under `output/`.

## Add A Publishing Feature

A bundled feature must be activated with the complete snippet in the
[optional-feature catalogue](../publishing/features/README.md). Longform Kit
does not auto-discover feature directories.

A downstream-specific title page, epigraph, post-processor, or similar feature
is executable publication code. Keep its files together under a descriptive
directory such as `publishing/features/epigraph/`, rather than mixing them into
`style/` or the manuscript.

Register the feature from `_quarto-custom.yml`. Use `publishing/filters/` only
for filters that are part of the generic Longform Kit build. Keep feature tests
under `publishing/tests/` and exercise every public output that the feature
affects. Give each downstream-added directory its own README and explicit
ownership; never infer ownership from the `publishing/features/` parent.

For an external Quarto extension, install it from the project root:

```sh
quarto add OWNER/EXTENSION
```

Inspect and commit the installed `_extensions/` files so routine builds remain
offline and reproducible.

Prefer semantic Markdown when content must survive PDF, DOCX, and GFM. Use
Quarto conditional Divs for genuinely format-specific material:

```markdown
::: {.content-visible when-format="gfm"}
This paragraph appears only in the combined Markdown edition.
:::

::: {.content-hidden when-format="gfm"}
This paragraph is omitted from that edition.
:::
```

Use Quarto's page-break shortcode for a deliberate break:

```markdown
{{< pagebreak >}}
```

After adding a filter, shortcode, extension, template, or post-processor, run
the complete build and inspect all four outputs:

```sh
python3 publishing/tests/test_build.py
quarto run publishing/longform.ts build
```

## Adjust Editorial Rules

Record document-facing conventions in `style/editorial.md`. Vale's executable
house rules remain under `.vale/styles/Academic/`; update them when the stated
policy changes. `.vale.ini` keeps proselint at suggestion level.

Harper's document dictionary is `.harper/dictionary.txt`. Add a term only when
it is accepted specialist vocabulary or a proper name in the manuscript. Do
not populate it from toolkit documentation or publishing code.

Root `.markdownlint.json` extends the Prettier-compatible Markdownlint style.
Override individual rules there only when the writing or documentation
structure requires it.
