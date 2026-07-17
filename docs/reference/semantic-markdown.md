# Authoring Markdown

Author files use ordinary Pandoc Markdown plus documented Quarto syntax.

## Epigraphs

Longform Kit vendors Fancy Epigraphs v0.0.1. Use its shortcode in front matter
or directly below a chapter heading:

```markdown
{{< epigraph "Do or **do not**. There *is* no try." source="Yoda" >}}
```

The `source` argument is optional. Quote both arguments, and use Markdown inside
them when needed. The extension renders a LaTeX `\epigraph` for PDF/LaTeX and a
portable blockquote for DOCX and GFM. It intentionally does not expose the
legacy Longform width, separator, blank-page, or Word-style switches.

## Page Breaks

Use Quarto's native page-break shortcode:

```markdown
{{< pagebreak >}}
```

Do not use raw LaTeX or a `.pagebreak` Div for portable content.

## Bibliography

Keep the bibliography target in `document/references.md`:

```markdown
# Bibliography {.unnumbered}

::: {#refs}
:::
```

Quarto citeproc fills `Div#refs`; do not hand-write entries inside it.

## Conditional Content

Use Quarto's native format conditionals:

```markdown
::: {.content-visible when-format="gfm"}
This paragraph appears only in the combined Markdown edition.
:::

::: {.content-hidden when-format="gfm"}
This paragraph is omitted from that edition.
:::
```

The standalone GFM renderer runs through Quarto, so these conditionals and
extension shortcodes are expanded before Markdown is written.

## Citations

Use standard Pandoc citations:

```markdown
[@key]
[@key, 10-12]
[@first; @second]
Author [-@key] argues ...
```

Citation IDs must exactly match `id` values in `references/library.json`.
