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

No optional features are bundled yet.

Bundled generalized features are MIT-licensed Longform Kit infrastructure. A
downstream repository may add author-owned feature directories, but it must
state ownership for each directory rather than reserving or assigning the
whole `publishing/features/` tree.
