---
name: verify-citations
description: Check, add, repair, or investigate citations in a Longform Kit project using Zotero, Better BibTeX citation keys, the configured CSL JSON export, and a chosen CSL style. Use for missing keys, duplicate keys, uncertain bibliographic metadata, citation rendering, or bibliography problems.
---

# Verify Citations

Treat Zotero as the bibliographic source of truth. `_quarto.yml.local` points
directly to a user-local Better CSL JSON export and CSL style; never repair or
replace either input by hand.

## Workflow

1. Read `_quarto.yml.local` without exposing its absolute paths in commits or
   reports. Confirm `bibliography` names the exact Better CSL JSON export – not
   a Zotero data directory or `zotero.sqlite` – and that `csl` names a readable
   CSL file.
2. Match cited keys in author Markdown against `id` values in the configured
   JSON. Check for malformed data, duplicate IDs, and cited IDs absent from the
   export. Use a structured JSON tool rather than editing or searching a
   minified export by hand.
3. For uncertain titles, contributors, dates, DOIs, item types, or locators,
   verify the item in Zotero or an available read-only Zotero connector. Do not
   infer bibliographic details from memory.
4. Correct the Zotero item or add it to the project collection.
5. Let the Better CSL JSON auto-export update its configured file; never repair
   generated JSON directly.
6. Run `quarto run scripts/longform.ts build` when citation formatting matters,
   then inspect the affected rendered citation and bibliography. Citation
   inputs are not versioned, so keep an archival snapshot separately when exact
   reproduction is required.

Use Pandoc citation forms, for example:

```markdown
[@key]
[@key, 42]
[@first; @second]
Author [-@key] argues ...
```

Change citation presentation by changing the `csl` path in ignored
`_quarto.yml.local`, not by adding hand-formatted notes or bibliography
entries.
