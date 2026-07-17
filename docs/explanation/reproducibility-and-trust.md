# Reproducibility And Trust

Longform Kit treats a document repository as an executable publishing project.
Its manuscript and build configuration are versioned, but its Zotero library
export and citation style are live machine-local inputs.

## Versioned And Live Sources

The chapter order, stable bibliography and CSL link paths, format settings,
pinned extension, scripts, and DOCX reference document live in the repository.
The Better CSL JSON export and installed Zotero styles do not.

`bin/longform setup` creates ignored links from `references/` to those external
files. Every machine and CI checkout must run setup. Zettlr separately needs
the same Better CSL JSON export selected in its citation preferences.

The links are live: Better BibTeX export updates and Zotero style updates affect
the next build. This keeps Zotero authoritative and avoids committing personal
libraries, but it does not provide Git-pinned citation reproducibility. Output
can change with no repository diff.

Once the linked files exist, Quarto and Pandoc can build without Zotero running
and without network access. Reproducing an earlier citation result still
requires the same external export and style versions.

## Generated Boundaries

Source and output have different ownership:

- Edit Markdown, `_quarto.yml`, and intentional project style assets.
- Edit bibliographic metadata and installed citation styles through Zotero;
  allow Better BibTeX to refresh its export.
- Generate the ignored citation links with `bin/longform setup`.
- Generate `document/.ztr-directory` from Quarto configuration.
- Ignore routine `build/`, `.cache/`, and `.quarto/` state.
- Preserve intentional submitted versions separately when archival policy
  requires them.

Patching a DOCX, PDF, or generated TeX file may fix one artefact while leaving
the other formats wrong. Fix the owning source or transformation instead.

## Versioned Executable Inputs

The vendored Quarto extension makes the build durable, but it executes Lua.
The TypeScript project helper and Agent Skills can also direct tools and
commands. Review changes to all of them with the same care as application code.

Quarto extensions should remain checked in at a known version. Upgrade them
deliberately, inspect the diff, and render all formats before accepting the new
version.

## Provider Independence

`AGENTS.md` describes repository rules in a neutral format, and Agent Skills
encode repeatable procedures. The underlying operations remain ordinary CLI
commands. No build depends on a particular model, agent host, MCP server, or API
credential.

Optional connectors can improve research, especially citation verification,
but they are outside the reproducibility boundary. Prefer read-only access and
never commit connector credentials.

## Meaningful Reproduction

Binary identity is not the goal for office documents and typeset PDFs across
different systems. Acceptance should instead check:

- Complete content, citations, notes, and heading hierarchy.
- Title, epigraph, TOC, chapter, and bibliography order.
- Page geometry, typography, and recto behavior.
- DOCX styles, TOC field, page breaks, and bibliography formatting.
- No missing or duplicated citation keys.

Those structural and visual invariants are meaningful to an author. Compare
them against a known export and style when exact citation reproduction matters.
