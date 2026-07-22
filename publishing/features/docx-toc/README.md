# DOCX table-of-contents refresh

## Status: optional and disabled by default

The post-render hook is registered only by a custom profile and remains a
no-op unless `LONGFORM_REFRESH_DOCX_TOC=1` is also set.

## Purpose and affected outputs

The feature asks LibreOffice through UNO to update cached entries and page
numbers for live table-of-contents fields in generated DOCX files. It contains
no thesis-specific typography or note policy and affects no other output.

## Requirements and external dependencies

Python 3 is always required. LibreOffice (or `soffice`) and its Python UNO
module are conditional dependencies only when refresh is requested.

## Complete `_quarto-custom.yml` activation snippet

```yaml
project:
  post-render:
    - publishing/features/docx-toc/refresh.py
```

Run a refresh with:

```sh
LONGFORM_REFRESH_DOCX_TOC=1 quarto run publishing/longform.ts build
```

## Metadata or Markdown interface

There is no manuscript interface. Quarto supplies newline-separated output
paths through `QUARTO_PROJECT_OUTPUT_FILES`; only paths ending in `.docx` are
opened.

## Compatibility and ordering

With all supported DOCX features, run after academic title, epigraph, and DOCX
typography preparation, but before DOCX typography stabilisation.

## Disable or uninstall

Unset `LONGFORM_REFRESH_DOCX_TOC` to skip refresh for one build. Remove the
post-render path to disable the feature completely.

## Failure behaviour

Disabled execution and builds with no DOCX output are no-ops. When explicitly
enabled, missing LibreOffice, missing UNO, listener failure, or save failure
stops the build. A temporary file is replaced only after a successful save.

## Verification command

```sh
python3 publishing/tests/test_optional_features.py docx-toc
```

Set `LONGFORM_TEST_DOCX_REFRESH=1` on Linux to include the real LibreOffice/UNO
integration case.

## Ownership and licence

This generalized bundled feature is Longform Kit infrastructure licensed under
the MIT terms in the repository `LICENSE`.
