# DOCX typography

## Status: optional and disabled by default

This alternate publication design is inert until its reference document and
hooks are registered explicitly. It is not the default Longform Kit DOCX.

## Purpose and affected outputs

The feature applies mirrored A4 geometry, EB Garamond typography, heading and
note hierarchy, bibliography treatment, odd-page top-level sections, folios,
and link styling to DOCX only. It derives section expectations from the
rendered document instead of assuming particular chapter or page-break counts.
Academic-title and front-epigraph markers are conditional integrations.

## Requirements and external dependencies

Preparation and stabilisation use Python 3's standard library. Font embedding
is a separate opt-in: set `LONGFORM_EMBED_DOCX_FONTS=1`, and provide the six
checksummed EB Garamond 1.001 OTF sources at the documented system location or
through an absolute `LONGFORM_EB_GARAMOND_DIR`. No font source is read when
embedding is off.

## Complete `_quarto-custom.yml` activation snippet

```yaml
project:
  post-render:
    - publishing/features/docx-typography/prepare.py
    - publishing/features/docx-typography/stabilize.py
format:
  docx:
    reference-doc: publishing/features/docx-typography/reference.docx
```

## Metadata or Markdown interface

The feature uses standard title, author, language, subject, and keyword
metadata, ordinary H1 headings, footnotes, block quotations, bibliography
paragraphs, and links. It recognizes academic-title and epigraph styles only
when those independent features are also active.

## Compatibility and ordering

For all features together, run academic title and epigraph processors first,
then `prepare.py`, optional `docx-toc/refresh.py`, and `stabilize.py`. The
stabilizer must be last because it verifies layout after third-party rewriting.

## Disable or uninstall

Remove the alternate `reference-doc` and both hooks from
`_quarto-custom.yml`. Generated documents then use the unchanged core
`publishing/docx/reference.docx`.

## Failure behaviour

Malformed OOXML, missing package members, duplicate optional markers, layout
drift, invalid embedding flags, missing fonts, prohibited embedding bits, and
font checksum mismatches fail closed. All package writes are atomic and
repeatable.

## Verification command

```sh
publishing/features/docx-typography/build_reference.py --check
python3 publishing/tests/test_optional_features.py docx-typography
```

## Ownership and licence

The generalized code and generated reference document are Longform Kit
infrastructure under the repository MIT licence. EB Garamond is not bundled;
its source project is licensed under the SIL Open Font License 1.1, summarized
in `fonts/README.md`.
