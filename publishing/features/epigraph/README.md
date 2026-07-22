# Epigraph

## Status: optional and disabled by default

This bundled feature is inert until its filter, PDF header, and DOCX processor
are registered explicitly. Longform Kit does not auto-discover it.

## Purpose and affected outputs

The feature renders semantic front and chapter epigraphs in PDF and DOCX while
preserving their Markdown structure in reflowable output. Its DOCX processor
adds only the styles needed by the filter, so the unchanged core reference
document is sufficient.

## Requirements and external dependencies

The Lua filter and PDF header require Pandoc/Quarto and LaTeX's `epigraph`
package. The DOCX processor requires only Python 3's standard library.

## Complete `_quarto-custom.yml` activation snippet

```yaml
project:
  post-render:
    - publishing/features/epigraph/docx.py
filters:
  - publishing/features/epigraph/filter.lua
format:
  pdf:
    include-in-header:
      - file: publishing/features/epigraph/pdf.tex
```

## Metadata or Markdown interface

Use two block quotes inside `.epigraph` or `.front-epigraph`. Supported
attributes are `width`, `separator`, `blank-before`, `oddpage`, `clear-after`,
`pagebreak-before`, `pagebreak-after`, and `leading-break`. DOCX widths are
`.60`, `.75`, or `1`; PDF accepts any decimal fraction above zero and at most
one.

```markdown
::: {.epigraph width=".75" separator="true"}
> Quotation.

> — Attribution
:::
```

## Compatibility and ordering

List the epigraph filter after academic title page. Run `epigraph/docx.py`
after the academic title processor and before DOCX typography, TOC refresh,
and stabilisation.

## Disable or uninstall

Remove all three feature paths from `_quarto-custom.yml`; the directory can
then be deleted safely.

## Failure behaviour

Malformed quote/source structure, invalid booleans or widths, multiple front
epigraphs, invalid OOXML, and corrupt packages fail closed. DOCX replacement is
atomic.

## Verification command

```sh
python3 publishing/tests/test_optional_features.py epigraph
```

## Ownership and licence

This generalized bundled feature is Longform Kit infrastructure licensed under
the MIT terms in the repository `LICENSE`.
