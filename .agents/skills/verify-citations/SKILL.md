---
name: verify-citations
description: Check, add, repair, or investigate citations in a Longform Kit project using Zotero, Better BibTeX citation keys, the configured CSL JSON export, and an installed Zotero CSL style. Use for missing keys, duplicate keys, uncertain bibliographic metadata, citation rendering, or bibliography problems.
---

# Verify Citations

Treat Zotero as the bibliographic source of truth. `references/library.json`
and `references/style.csl` are ignored live links to user-local inputs; never
repair or replace their targets by hand.

## Workflow

1. Confirm `bin/longform setup` has linked the intended Better CSL JSON export
   and installed Zotero style. `--library` accepts the exact export file or a
   directory containing `library.json`; this is a Better BibTeX export
   location, not Zotero's data directory or `zotero.sqlite`. Root `_quarto.yml`
   deliberately contains only the stable link paths.
2. Run `bin/longform check`. It detects missing local setup, malformed
   bibliography data, duplicate IDs, and cited IDs missing from the export.
3. For uncertain titles, contributors, dates, DOIs, item types, or locators,
   verify the item in Zotero or an available read-only Zotero connector. Do not
   infer bibliographic details from memory.
4. Correct the Zotero item or add it to the project collection.
5. Let the Better CSL JSON auto-export update its configured source file;
   never repair that JSON by hand.
6. Rerun `bin/longform check` and render an affected output when citation
   formatting matters. Citation inputs are not versioned, so preserve an
   archival snapshot separately when exact reproduction is required.

Use Pandoc citation forms, for example:

```markdown
[@key]
[@key, 42]
[@first; @second]
Author [-@key] argues ...
```

Change citation presentation by selecting another installed Zotero style with
`bin/longform setup --style STYLE`, not by adding hand-formatted notes or
bibliography entries.
