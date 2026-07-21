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

The defaults leave headings unnumbered and include chapters only in the table
of contents. A downstream that needs numbered sections or a deeper contents
list can opt in explicitly:

```yaml
toc-depth: 2
number-sections: true
```

EB Garamond is also assigned to the PDF mono family by default. Override
`format.pdf.monofont` when source code must retain fixed-width alignment.

The starter sets the shared PDF type area with
`\areaset[current]{140mm}{227mm}` in `_quarto.yml`. Change both dimensions
together and inspect both PDFs when a downstream needs a different measure or
page depth. Adjust `linestretch` with the measure rather than in isolation:
longer lines generally need more leading, while shorter lines need less.

The non-standard 15.25 pt body size is a keyed KOMA class option in both PDF
profiles. Keep `fontsize=15.25pt` in both class-option strings when changing
other profile-specific options; Quarto's bare `fontsize` field does not make
this arbitrary size effective. The shared header also sets footnotes to
11.4/15.25, uses KOMA's `\deffootnote` for full-size hanging labels, and removes
the separator rule while retaining the ordinary whitespace above the notes.
Change these three decisions together if a downstream needs a different note
hierarchy. KOMA's `footinclude`, `footheight`, and `footlines` settings concern
the page footer, not footnotes.

The binding profile deliberately starts with `BCOR=0mm`. Once a printer or
binding method supplies the width of paper lost at the spine, replace only that
value, for example:

```yaml
format:
  pdf:
    classoption: "twoside,openright,BCOR=8mm,fontsize=15.25pt"
```

Do not use `BCOR` merely to request a wider-looking gutter. The shared
`areaset[current]` preserves a replacement binding correction automatically.
A downstream that prefers KOMA's divisor construction can remove `areaset` and
add the same `DIV` option to both PDF profiles; the binding profile's
`classoption` scalar replaces the shared value. Quarto's `geometry` option is
still available for a downstream that intentionally wants to bypass KOMA.

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
