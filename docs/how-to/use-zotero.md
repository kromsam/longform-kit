# Connect A Zotero Collection

## Configure Better BibTeX

1. Install Zotero and Better BibTeX.
2. Create or select the collection for the document.
3. Export it with the **Better CSL JSON** translator.
4. Save it as root `references/library.json`.
5. Enable **Keep updated**.
6. Commit the export so builds remain offline.

Better BibTeX auto-export runs while Zotero is available; it is not part of the
rendering pipeline.

## Pin The Citation Style

Save the exact style as `references/style.csl` and configure root `_quarto.yml`:

```yaml
bibliography: references/library.json
csl: references/style.csl
```

Do not point at a Zotero profile or home-directory file.

## Cite And Check

Use Better BibTeX keys in author Markdown:

```markdown
A single source can anchor a specific claim [@authorTitle2026, 44-46].
Several accounts disagree [@firstKey; @secondKey].
```

Run `bin/longform check`. It fails for malformed CSL JSON, duplicate item IDs,
or cited keys absent from the export. Correct metadata in Zotero, allow the
auto-export to update, review the diff, and check again; never repair generated
CSL JSON by hand.
