---
name: build-and-export
description: Build, validate, or troubleshoot a Longform Kit document and its PDF, binding PDF, DOCX, LaTeX, or GFM outputs. Use for export requests, build failures, output verification, chapter-order changes, or Zettlr project synchronization.
---

# Build And Export

Work from the repository root and use `bin/longform`; do not reproduce its
Quarto or Pandoc commands manually.

## Workflow

1. Read `AGENTS.md`, the root `_quarto.yml` discovery loader, and
   `quarto/project.yml`. Read `quarto/binding.yml` when the binding PDF is in
   scope.
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

6. Confirm the expected files under `build/` are non-empty. For layout
   changes, inspect the rendered PDF or DOCX rather than relying only on exit
   status.

## Guardrails

- Never patch generated outputs. Fix Markdown, `quarto/project.yml`,
  `quarto/binding.yml`, the reference DOCX, or vendored extension source under
  `quarto/extensions/` as appropriate. Edit root `_quarto.yml` only when the
  metadata-file composition changes.
- Keep the ordinary PDF settings and binding PDF overlay distinct.
- GFM is assembled as a temporary standalone Quarto document because Quarto
  books do not have a combined GFM format. Confirm that shortcodes and
  `when-format="gfm"` conditionals were expanded in the generated Markdown.
- When `longform.required-fonts` is configured, treat a failing `doctor` font
  check as a build blocker rather than accepting a substituted family.
- Report missing dependencies or unverified visual behavior explicitly.
