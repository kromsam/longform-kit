# Migrate To v0.7

Longform Kit v0.7 completes the work deferred from v0.6: the imposed two-up
PDF regains its discovery metadata and bookmarks, the combined Markdown
edition gains an explicit document identity, and repeated builds can be made
byte-identical. Adopters should expect changed default bytes in the two-up
PDF, the combined Markdown edition, and PDF heading text even when they change
no configuration.

## Install qpdf

The two-up PDF now requires qpdf 11.10 or newer next to `pdfjam`. Earlier
qpdf releases cannot resolve every outline destination emitted by current
LaTeX PDF management, so the build refuses them. `PDFJAM`, `QPDF`, and
`LUALATEX` may name alternate executables when the defaults on `PATH` are not
suitable.

## Default Output Changes

The two-up PDF now retains title, author, subject, keywords, and document
language, and remaps every source bookmark onto its imposed sheet while
preserving outline order and nesting. The build reads the source outline with
qpdf and restores the metadata through a two-pass LuaLaTeX wrapper. Because
imposition discards the source structure tree, the print derivative remains
intentionally untagged and continues to make no PDF/A or PDF/UA claim.

The combined Markdown edition now begins with JSON-safe YAML discovery
metadata for title, subtitle, title-meta, author, date, language, subject, and
keywords, followed by one visible document-title heading, the subtitle as an
italic paragraph, and the author and date. Citations, includes, shortcodes,
conditional content, and media extraction are unchanged.

PDF headings now render Pandoc's TeX quote and dash forms as typographic
characters, so quotation marks and dashes in headings extract correctly from
both PDFs.

The build also removes Quarto's root-level `index-luamml-mathml.html` sidecar
during cleanup, whether the build succeeds or fails.

## Build Reproducibly When Needed

Set the standard `SOURCE_DATE_EPOCH` environment variable to the same Unix
timestamp for every comparison build:

```sh
SOURCE_DATE_EPOCH=1704067200 quarto run publishing/longform.ts build
```

With identical sources, tool versions, and build environments, all four
outputs are then byte-identical, and the two-up trailer identifier is derived
from the source PDF. Without `SOURCE_DATE_EPOCH`, creation metadata and PDF
identifiers may legitimately differ between builds, as before.

## Run The Optional-Feature Suite With Custom Profiles

`python3 publishing/tests/test_optional_features.py` now permits committed
downstream settings in `_quarto-custom.yml`. The explicit `starter-contract`
argument retains the stricter official-starter check that no optional feature
is enabled by default; official Longform Kit CI runs both. A downstream with a
customized profile should run the default suite and leave `starter-contract`
to upstream.

For PDF-only appendices from supplied PDF documents, follow the verified
`pdfpages` workflow in [Customize the project](customization.md), including
its non-PDF and archival-validation caveats.

## Adopt And Verify The Release

Merge the tag so the downstream retains shared Git ancestry:

```sh
git fetch upstream --tags
git switch main
git pull --ff-only origin main
git switch -c chore/sync-longform-v0.7.0
git merge --no-ff --no-edit v0.7.0
```

Then run:

```sh
quarto run publishing/longform.ts zettlr
python3 publishing/tests/test_build.py
python3 publishing/tests/test_optional_features.py
quarto run publishing/longform.ts build
git merge-base --is-ancestor v0.7.0 HEAD
```

For release acceptance, also run strict veraPDF validation when it is in
downstream scope, verify one repeated build with a fixed `SOURCE_DATE_EPOCH`
for byte-identical outputs, then inspect both PDFs, the DOCX, and the combined
Markdown identity manually.
