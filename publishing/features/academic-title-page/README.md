# Academic title page

## Status: optional and disabled by default

This bundled feature has no effect until every required path below is copied
into `_quarto-custom.yml`. Longform Kit does not auto-discover features.

## Purpose and affected outputs

The feature replaces the PDF title composition and adds matching semantic
fields and styles to DOCX. It leaves GFM content unchanged. Standard `title`,
`subtitle`, `author`, and `date` metadata are reused.

## Requirements and external dependencies

PDF requires the core `publishing/pdf/typography.tex` header because the title
uses `\LongformSemibold`. DOCX processing uses Python 3's standard library and
does not require DOCX typography, LibreOffice, or font files.

## Complete `_quarto-custom.yml` activation snippet

```yaml
project:
  post-render:
    - publishing/features/academic-title-page/docx.py
filters:
  - publishing/features/academic-title-page/filter.lua
format:
  pdf:
    template-partials:
      - publishing/features/academic-title-page/title.tex
```

## Metadata or Markdown interface

Configure the feature through one nested object. Every administrative field is
optional; the two labels have English defaults.

```yaml
academic-title-page:
  student-number: "12345678"
  degree: "MA Thesis International Dramaturgy"
  supervisor: "Dr A. Example"
  institute: "Example University"
  labels:
    student-number: "Student number"
    supervisor: "Under supervision of"
```

## Compatibility and ordering

When combined with epigraphs, list the academic filter first and run
`academic-title-page/docx.py` before `epigraph/docx.py`. In the complete DOCX
pipeline it precedes DOCX typography, TOC refresh, and stabilisation.

## Disable or uninstall

Remove the filter, template partial, and post-render path from
`_quarto-custom.yml`. The directory may then be deleted without affecting core
builds.

## Failure behaviour

A missing or non-object `academic-title-page` configuration, duplicate DOCX
title fields, invalid OOXML, or an incomplete DOCX package fails the build.
Atomic replacement preserves the original package on processor failure.

## Verification command

```sh
python3 publishing/tests/test_optional_features.py academic-title-page
```

## Ownership and licence

This generalized bundled feature is Longform Kit infrastructure licensed under
the MIT terms in the repository `LICENSE`.
