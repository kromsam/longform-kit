---
name: verify-citations
description: Check, add, repair, or investigate citations in a Longform Kit project using Zotero, Better BibTeX citation keys, project-local CSL JSON, and the pinned CSL style. Use for missing keys, duplicate keys, uncertain bibliographic metadata, citation rendering, or bibliography problems.
---

# Verify Citations

Treat Zotero as the bibliographic source of truth and
`document/references/library.json` as a generated project export.

## Workflow

1. Read the citation syntax and bibliography paths in `document/_quarto.yml`.
2. Run `bin/longform check`. It detects malformed bibliography data, duplicate
   IDs, and cited IDs missing from the project export.
3. For uncertain titles, contributors, dates, DOIs, item types, or locators,
   verify the item in Zotero or an available read-only Zotero connector. Do not
   infer bibliographic details from memory.
4. Correct the Zotero item or add it to the project collection.
5. Let the Better CSL JSON auto-export update
   `document/references/library.json`; never repair that JSON by hand.
6. Review the export diff, rerun `bin/longform check`, and render an affected
   output when citation formatting matters.

Use Pandoc citation forms, for example:

```markdown
[@key]
[@key, 42]
[@first; @second]
Author [-@key] argues ...
```

Change citation presentation by replacing the pinned project CSL deliberately,
not by adding hand-formatted notes or bibliography entries.
