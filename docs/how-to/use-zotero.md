# Connect A Zotero Collection

Use a dedicated Zotero collection so the repository contains only references
needed by the document, not an entire personal library.

## Configure Better BibTeX

1. Install Zotero and the Better BibTeX extension.
2. Create or select the collection for the document.
3. Export that collection with the **Better CSL JSON** translator.
4. Save it as `document/references/library.json`.
5. Enable **Keep updated** so Better BibTeX refreshes the file when collection
   items change.
6. Commit the exported JSON so builds do not require Zotero.

Better BibTeX auto-export runs while Zotero is available. It is not part of the
rendering pipeline.

## Pin The Citation Style

Export or obtain the exact CSL style used by the project and save it as
`document/references/style.csl`. Configure both local paths in
`document/_quarto.yml`:

```yaml
bibliography: references/library.json
csl: references/style.csl
```

Do not point the project at a file inside a Zotero profile or a home directory.

## Cite Sources

Use Better BibTeX citation keys in the Markdown:

```markdown
Forensic practice is contested [@authorTitle2026, 44-46].

Several accounts disagree [@firstKey; @secondKey].
```

Run:

```sh
bin/longform check
```

The command fails for duplicate bibliography IDs or cited keys absent from the
export.

## Correct Metadata

Correct an item in Zotero, allow the auto-export to update, review the JSON
diff, and run `check` again. Never hand-edit generated CSL JSON. When metadata is
uncertain, verify it through Zotero, a DOI registry, a library catalogue, or an
available read-only connector rather than guessing.

See the Better BibTeX
[export documentation](https://retorque.re/zotero-better-bibtex/exporting/)
for translator and auto-export details.
