# Semantic Markdown Reference

Longform Kit uses Pandoc fenced Divs to express document intent before an output
format is selected.

## Front Epigraph

Place at most one top-level front epigraph in `index.qmd`:

```markdown
::: {.front-epigraph width=".60" blank-before="true" oddpage="true" pagebreak-before="true" pagebreak-after="true"}
> Quotation text.

> -- Attribution
:::
```

It must contain exactly two Markdown blockquotes: quotation, then attribution.
The filter places it between the title page and TOC in PDF and LaTeX, and before
the generated TOC field in DOCX.

Supported attributes:

| Attribute | Purpose |
| --- | --- |
| `width` | Decimal fraction of the PDF text width; default `.75` |
| `blank-before` | Add a blank PDF/LaTeX page before the epigraph |
| `oddpage` | Start the PDF/LaTeX epigraph on a recto page |
| `clear-after` | Clear the PDF/LaTeX page after the epigraph |
| `pagebreak-before` | Add a DOCX page break before the epigraph |
| `pagebreak-after` | Add a DOCX page break after the epigraph |
| `leading-break` | Begin the DOCX quotation with a line break; defaults to `false` |
| `docx-flush` | Apply the bundled `Epigraph Text Flush` style instead of `Epigraph Text` |
| `docx-quote-style` | Apply another named DOCX paragraph style to the quotation |
| `docx-source-style` | Apply another named DOCX paragraph style to the attribution |

Boolean attributes accept only `true` or `false`.

## Chapter Epigraph

Place a top-level epigraph directly after a chapter heading:

```markdown
::: {.epigraph width=".60" separator="true"}
> Quotation text.

> -- Attribution
:::
```

The same two-blockquote rule applies. `separator`, which defaults to `true`,
controls the rule below a chapter epigraph in PDF, LaTeX, and DOCX. DOCX applies
the `Epigraph Text` and `Epigraph Source` styles by default and applies `First
Paragraph` to an immediately following prose paragraph. Set
`leading-break="true"` only when reproducing an established DOCX layout.

Set `docx-flush="true"` when one quotation should align with the body margin
without changing every epigraph style. `docx-quote-style` and
`docx-source-style` accept names from the configured reference DOCX and override
the bundled style names. A custom reference document must preserve `Epigraph
Text`, `Epigraph Text Flush`, `Epigraph Source`, and `First Paragraph` unless the
source selects replacements explicitly.

## Page Break

Use an empty Div:

```markdown
::: {.pagebreak}
:::
```

Content inside a page-break Div is an error. The bundled filter writes an
appropriate break for PDF, LaTeX, DOCX, and GFM.

## Bibliography

Keep the bibliography location in `references.md`:

```markdown
# Bibliography {.unnumbered}

::: {#refs}
:::
```

Citeproc fills `Div#refs`. Do not hand-write entries inside it.

## Conditional Content

Use Quarto's format conditionals. Markdown-derived GFM supports
`content-visible` and `content-hidden` with `when-format="gfm"` or
`when-format="markdown"`:

```markdown
::: {.content-visible when-format="gfm"}
This paragraph appears only in the GFM output.
:::

::: {.content-hidden when-format="gfm"}
This paragraph is omitted from GFM.
:::
```

These GFM-specific conditionals require `longform.gfm-source: markdown`, which
is the default. With `gfm-source: latex`, Quarto has already resolved
conditionals for the LaTeX target before Pandoc converts the result to GFM. Use
the LaTeX source only when compatibility with that canonical export matters
more than GFM-only conditional content.

Avoid raw LaTeX for content that must survive in DOCX or Markdown-derived GFM.

## Citations

Use standard Pandoc citations:

```markdown
[@key]
[@key, 10-12]
[@first; @second]
Author [-@key] argues ...
```

Citation IDs must exactly match `id` values in the Better CSL JSON export.
Pandoc normally determines note placement around punctuation. A migrated
document that historically attached a citation directly to the preceding word
and rendered its note before immediately following punctuation can enable
`longform.preserve-attached-note-positions`. It is an opt-in compatibility rule,
not a general citation-style setting.
