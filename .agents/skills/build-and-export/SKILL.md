---
name: build-and-export
description: Build, validate, or troubleshoot a Longform Kit document and its ordinary PDF, binding PDF, DOCX, or combined GFM outputs. Use for export requests, build failures, output verification, chapter-order changes, or Zettlr project synchronization.
---

# Build And Export

Work from the repository root. The canonical command is the small project
program; plain `quarto render` does not create the complete output set.

## Workflow

1. Read `AGENTS.md`, `_quarto.yml`, and `document/chapters.yml`. Read
   `_quarto-binding.yml` when PDF layout is in scope.
2. Confirm ignored `_quarto.yml.local` names readable absolute `bibliography`
   and `csl` paths. Never commit or rewrite another user's local paths.
3. After chapter-order, title, or CSL-path changes, refresh the optional Zettlr
   project:

   ```sh
   quarto run scripts/longform.ts zettlr
   ```

4. Build every deliverable:

   ```sh
   quarto run scripts/longform.ts build
   ```

5. Confirm the ordinary PDF, binding PDF, DOCX, and combined GFM files under
   `build/` are non-empty. For layout changes, inspect rendered documents
   rather than relying only on exit status.

## Guardrails

- Never patch generated outputs. Fix Markdown, root Quarto configuration, the
  reference DOCX, or an explicitly installed extension as appropriate.
- Keep the symmetric-margin ordinary PDF and mirrored-margin binding profile
  distinct; KOMA-Script calculation is the starter default, downstreams may
  deliberately set explicit geometry, and both profiles retain blank verso
  pages for recto chapter starts.
- The GFM edition is assembled as a temporary standalone Quarto document
  because Quarto books do not have a native combined GFM format. Confirm that
  citations, shortcodes, `when-format="gfm"` conditionals, and media paths are
  resolved in the generated Markdown.
- LaTeX is an internal PDF concern, not a public output.
- Report missing dependencies or unverified visual behaviour explicitly.
