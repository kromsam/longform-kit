# Customize Outputs

Use documented Quarto options in `quarto/project.yml`; Longform Kit does not
define parallel format names or rendering settings. Keep root `_quarto.yml` as
the required project loader.

## Change The Output Name

```yaml
book:
  output-file: "my-dissertation"
```

Use a basename without an extension. The CLI appends `-binding` to the binding
PDF automatically.

## Override PDF Options

```yaml
format:
  pdf:
    mainfont: "EB Garamond"
    sansfont: "Fira Sans"
    fontsize: 12pt
    linestretch: 1.25
  docx:
    toc: true
    reference-doc: references/reference.docx
  latex:
    mainfont: "EB Garamond"
```

The `format` map is the complete native output list, so retain PDF, DOCX, and
LaTeX. Keep ordinary geometry in `quarto/project.yml` and binding geometry in
`quarto/binding.yml`.

Render the binding PDF through `bin/longform build pdf` (or `build all`). The
wrapper selects the `binding` profile and explicitly loads the relocated
metadata file. Bare `quarto render --profile binding` does not discover
`quarto/binding.yml`, because it is not a root `_quarto-binding.yml` file.

Declare production fonts that must not be substituted:

```yaml
longform:
  required-fonts:
    - EB Garamond
    - Fira Sans
```

`bin/longform doctor` verifies each family with Fontconfig.

## Customize DOCX Styles And TOC

Edit a project-owned copy of `references/reference.docx`, then keep the native
format pointed at it:

```yaml
format:
  docx:
    toc: true
    toc-depth: 2
    toc-title: Contents
    reference-doc: references/reference.docx
```

Quarto and Pandoc generate the Word TOC field and apply named styles from the
reference document. Open the result in Word or LibreOffice and refresh fields
when cached page numbers are stale.

## Customize Epigraph Typography

Fancy Epigraphs' LaTeX defaults live in
`quarto/extensions/epigraph/epigraph.tex`. Prefer adding a separate,
project-owned header after that file rather than modifying vendored code. For
DOCX, the shortcode emits ordinary blockquotes, so customize the `Block Text`
style in the reference document.

## Customize GFM

The GFM TOC uses the top-level `toc-depth` unless overridden:

```yaml
longform:
  gfm-toc-depth: 3
```

Other GFM behaviour comes from Quarto's native `gfm` format. There is no
LaTeX-derived or legacy-byte compatibility mode in Longform Kit 0.3.
