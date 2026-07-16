---
name: build-and-export
description: Build, validate, or troubleshoot a Longform Kit document and its PDF, binding PDF, DOCX, LaTeX, or GFM outputs. Use for export requests, build failures, output verification, chapter-order changes, or Zettlr project synchronization.
---

# Build And Export

Work from the repository root and use `bin/longform`; do not reproduce its
Quarto or Pandoc commands manually.

## Workflow

1. Read `AGENTS.md` and `document/_quarto.yml`.
2. Run `bin/longform doctor` when tool availability or versions are uncertain.
3. After chapter-order changes, run `bin/longform zettlr sync`.
4. Run `bin/longform check` before rendering.
5. Build the narrowest useful target:

```sh
bin/longform build pdf
bin/longform build docx
bin/longform build latex
bin/longform build gfm
bin/longform build all
```

6. Confirm the expected files under `document/build/` are non-empty. For layout
   changes, inspect the rendered PDF or DOCX rather than relying only on exit
   status.

## Guardrails

- Never patch generated outputs. Fix Markdown, `_quarto.yml`, the binding
  profile, reference DOCX, or vendored extension source as appropriate.
- Keep the ordinary and binding PDF profiles distinct.
- Remember that combined GFM is built by Quarto's bundled Pandoc, not Quarto's
  unsupported book-to-GFM route.
- Report missing dependencies or unverified visual behavior explicitly.
