# Customize The Project

The starter keeps only configuration needed by every document. Add optional
Quarto features in the conventional way and keep manuscript-specific policy in
your own repository.

## Change Shared Output Settings

Edit root `_quarto.yml` for settings shared by the project, such as paper size,
font size, table of contents depth, PDF typography, or the DOCX reference file.
Edit `_quarto-binding.yml` only when the binding PDF must differ.

Keep the binding profile's distinct `book.output-file` value. If you rename the
shared `book.output-file`, give the binding profile the corresponding
`-binding` name so one build cannot overwrite the other PDF.

For Word styles, edit a copy of `references/reference.docx` in Word or
LibreOffice and retain it at that tracked path. Quarto applies its named styles
when producing DOCX.

## Add Epigraphs

Epigraphs are not part of the default manuscript or configuration. To add the
Fancy Quarto Epigraphs extension, install it from the project root:

```sh
quarto add andrewheiss/fancy-epigraphs-quarto
```

Review and commit the installed `_extensions/` files so builds remain offline
and reproducible. The shortcode emits `\epigraph` for PDF, so add the package
and the preferred spacing to the existing `format.pdf` configuration in
`_quarto.yml`:

```yaml
format:
  pdf:
    include-in-header:
      text: |
        \usepackage{epigraph}
        \setlength{\epigraphrule}{0em}
        \setlength{\beforeepigraphskip}{-2em}
        \setlength{\afterepigraphskip}{1em}
```

Then use the extension's shortcode below a chapter heading or in front matter:

```markdown
{{< epigraph "Do or **do not**. There *is* no try." source="Yoda" >}}
```

The source is optional. The extension renders a portable blockquote in formats
such as DOCX and GFM. Because the combined GFM edition runs through Quarto,
registered shortcodes are expanded there as well.

If you implement an epigraph without an extension, prefer semantic Markdown
such as a block quote. Avoid raw LaTeX when the same passage must survive DOCX
and GFM conversion.

## Add Format-Specific Content

Use Quarto's native conditional Divs instead of embedding output-specific raw
markup:

```markdown
::: {.content-visible when-format="gfm"}
This paragraph appears only in the combined Markdown edition.
:::

::: {.content-hidden when-format="gfm"}
This paragraph is omitted from that edition.
:::
```

Use the native page-break shortcode when a deliberate break is needed:

```markdown
{{< pagebreak >}}
```

After adding a filter, shortcode, extension, or resource, run the complete
build and inspect all four outputs. A customization that works in PDF can still
degrade in DOCX or GFM.

## Adjust Editorial Rules

The Vale house style is under `.vale/styles/Academic/`. Edit those rules when
the document follows a different spelling, quotation, date, dash, or citation
policy. `.vale.ini` deliberately keeps proselint at suggestion level.

Harper's live project dictionary is `.harper/dictionary.txt`. Add a term only
when it is accepted specialist vocabulary or a proper name. The default file
contains only the toolkit's typography and publishing vocabulary, so the
template does not impose manuscript-specific language.

Root `.markdownlint.json` extends the Prettier-compatible Markdownlint style.
Override individual rules there only when the manuscript structure requires
it.
