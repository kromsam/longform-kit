# Migrate To v0.6

Longform Kit v0.6 establishes an explicit core-versus-optional feature
contract. It also changes the default PDF design and standards target, so
adopters should expect pagination and line-break differences even when they do
not enable an optional feature.

## Default Output Changes

The one-up PDF now uses the audited EB Garamond, microtype, heading, note, and
page-layout policy in `publishing/pdf/typography.tex` and targets PDF/A-4f by
default. PDF/A applies only to the one-up publication PDF. The imposed two-up
derivative remains intentionally untagged and makes no PDF/A or PDF/UA claim.

The core DOCX reference is byte-identical to its pre-v0.6 version. The
publication DOCX design is an optional alternate reference, not a default
change.

The PDF path requires a TeX distribution no older than June 2025 with
LuaLaTeX and the packages listed in the root README. PDF management is supplied
by the LaTeX core. Strict release validation remains opt-in through
`LONGFORM_VALIDATE_PDF=1` and requires Java 21 and veraPDF.

## Activate Optional Features Explicitly

Optional features live only under `publishing/features/`. Longform Kit does
not auto-discover or register them, and root `_quarto.yml` contains no optional
feature path. Copy a complete snippet from the
[optional-feature catalogue](../publishing/features/README.md) into the
downstream `_quarto-custom.yml`.

The canonical combined order is:

1. academic-title-page filter;
2. epigraph filter;
3. academic-title-page DOCX processor;
4. epigraph DOCX processor;
5. DOCX typography preparation;
6. optional DOCX TOC refresh;
7. DOCX typography stabilization.

The alternate DOCX reference belongs to the typography feature. The title-page
PDF partial and epigraph PDF header are registered separately, as shown in the
catalogue.

External processing is still explicit. `LONGFORM_EMBED_DOCX_FONTS=1` enables
checked EB Garamond embedding, and `LONGFORM_REFRESH_DOCX_TOC=1` enables the
LibreOffice/UNO field refresh. Merely activating either hook does not enable
those external operations.

## Update Title Metadata And Manuscript Markup

Academic title metadata is nested under `academic-title-page`:

```yaml
academic-title-page:
  student-number: "12345678"
  degree: Example degree
  supervisor: Dr A. Supervisor
  institute: Example University
```

The feature README documents optional labels. Epigraphs retain the existing
`.front-epigraph` and `.epigraph` classes and their supported attributes.

Remove `docx-flush` from manuscript conditional Divs. It is no longer part of
the documented feature interface; the independent DOCX processors and
typography hooks own the required layout transitions.

## Migrate Ownership Rules

Replace any wildcard ownership rule for `publishing/features/` with explicit
per-directory ownership. In v0.6, `_shared`, `academic-title-page`, `epigraph`,
`docx-typography`, and `docx-toc` are bundled MIT-licensed Longform Kit
infrastructure. A downstream-added feature may remain document-owned, but its
directory must state that ownership explicitly.

Continue resolving core build code, generic tests, fixtures, root `index.md`,
and the named bundled features in favour of upstream. Preserve downstream
writing, materials, style policy, custom activation, archives, and explicitly
owned feature directories.

## Adopt And Verify The Release

Merge the tag so the downstream retains shared Git ancestry:

```sh
git fetch upstream --tags
git switch main
git pull --ff-only origin main
git switch -c chore/sync-longform-v0.6.0
git merge --no-ff --no-edit v0.6.0
```

After resolving the ownership boundaries, run:

```sh
quarto run publishing/longform.ts zettlr
python3 publishing/tests/test_build.py
python3 publishing/tests/test_optional_features.py
quarto run publishing/longform.ts build
git merge-base --is-ancestor v0.6.0 HEAD
```

For release acceptance, also run strict veraPDF validation and the real
LibreOffice/UNO refresh when those paths are in downstream scope, then inspect
both PDFs and the DOCX manually.
