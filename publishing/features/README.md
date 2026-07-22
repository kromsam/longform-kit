# Optional Publishing Features

Longform Kit has an explicit boundary between core behaviour and optional
features:

```text
Core: lives outside publishing/features/, is registered in root _quarto.yml,
and is enabled in an unchanged checkout.

Optional: lives under publishing/features/<feature>/, is never referenced by
root _quarto.yml, and is enabled only by copying a documented snippet into
_quarto-custom.yml.
```

There is no auto-discovery, feature registry, or generated installer. Merely
placing a directory here has no runtime or output effect. Every immediate
feature directory must have a README containing:

- `Status: optional and disabled by default`
- `Purpose and affected outputs`
- `Requirements and external dependencies`
- `Complete _quarto-custom.yml activation snippet`
- `Metadata or Markdown interface`
- `Compatibility and ordering`
- `Disable or uninstall`
- `Failure behaviour`
- `Verification command`
- `Ownership and licence`

Directories beginning with an underscore are internal support code, not
activatable features, and must document that status in their own README.

## Catalogue

- `academic-title-page`: PDF composition plus independent DOCX fields and
  styles.
- `epigraph`: semantic front and chapter epigraphs across outputs.
- `docx-typography`: an alternate publication DOCX reference and deterministic
  preparation and stabilization policy.
- `docx-toc`: an opt-in LibreOffice/UNO refresh of cached DOCX table-of-contents
  entries and page numbers.

## Academic Title Page And Epigraph

Copy this complete snippet to activate both features in their supported order:

```yaml
project:
  post-render:
    - publishing/features/academic-title-page/docx.py
    - publishing/features/epigraph/docx.py
filters:
  - publishing/features/academic-title-page/filter.lua
  - publishing/features/epigraph/filter.lua
format:
  pdf:
    include-in-header:
      - file: publishing/features/epigraph/pdf.tex
    template-partials:
      - publishing/features/academic-title-page/title.tex
```

## All Supported Optional Features

Copy this complete snippet to activate every bundled feature in the canonical
combined order. The TOC step remains a no-op unless
`LONGFORM_REFRESH_DOCX_TOC=1`; DOCX font embedding remains off unless
`LONGFORM_EMBED_DOCX_FONTS=1`.

```yaml
project:
  post-render:
    - publishing/features/academic-title-page/docx.py
    - publishing/features/epigraph/docx.py
    - publishing/features/docx-typography/prepare.py
    - publishing/features/docx-toc/refresh.py
    - publishing/features/docx-typography/stabilize.py
filters:
  - publishing/features/academic-title-page/filter.lua
  - publishing/features/epigraph/filter.lua
format:
  pdf:
    include-in-header:
      - file: publishing/features/epigraph/pdf.tex
    template-partials:
      - publishing/features/academic-title-page/title.tex
  docx:
    reference-doc: publishing/features/docx-typography/reference.docx
```

Bundled generalized features are MIT-licensed Longform Kit infrastructure. A
downstream repository may add author-owned feature directories, but it must
state ownership for each directory rather than reserving or assigning the
whole `publishing/features/` tree.
