# Reproducibility And Trust

Longform Kit treats a document repository as an executable publishing project.
Reproducibility depends on keeping every input local, explicit, and reviewable.

## Local Sources

The chapter order, bibliography path, CSL path, format settings, extension,
filters, and DOCX reference document live in the repository. There are no
absolute paths to a user's home directory and no required global Zettlr export
profiles.

The Better CSL JSON file is generated but committed. This separates two times:

- **Research time:** Zotero and Better BibTeX update reference metadata.
- **Build time:** Quarto and Pandoc read the pinned local snapshot offline.

## Generated Boundaries

Source and output have different ownership:

- Edit Markdown, `_quarto.yml`, project CSL, and intentional style assets.
- Generate `.ztr-directory` from Quarto configuration.
- Ignore routine `build/` and `.quarto/` state.
- Preserve intentional submitted versions separately when archival policy
  requires them.

Patching a DOCX, PDF, or generated TeX file may fix one artefact while leaving
the other formats wrong. Fix the owning source or transformation instead.

## Versioned Executable Inputs

The vendored Quarto extension makes the build durable, but it also executes Lua
and TypeScript. Agent Skills can direct tools and commands. Review changes to
both with the same care as application code.

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

Those structural and visual invariants are stable enough to test and meaningful
to an author.
