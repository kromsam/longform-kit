---
name: lint-prose
description: Run and interpret prose linting for a Longform Kit manuscript with Vale, Harper, or Markdownlint. Use for copyediting, spelling and style checks, pre-submission cleanup, dictionary maintenance, or resolving prose-linter findings without damaging academic meaning or Markdown.
---

# Lint Prose

## Workflow

1. Read `AGENTS.md`, `.vale.ini`, and any project editorial style guide.
2. Run the installed tools that fit the task:

   ```sh
   vale sync
   vale document
   harper-cli lint -d british -u .harper/dictionary.txt document/*.md document/manuscript/*.md
   markdownlint-cli2 README.md "docs/**/*.md" "document/**/*.md"
   ```

   `vale sync` is needed after cloning to install the advisory proselint
   package. Report unavailable tools instead of silently treating them as
   passing.

3. Triage findings in context. The tracked `Academic` Vale style is the house
   policy; proselint is deliberately suggestion-only. Linters provide evidence,
   not editorial authority.
4. Make narrow source edits under `document/`; preserve quotations, citation
   keys, language attributes, Quarto shortcodes, conditional Divs, and
   technical terminology.
5. Add a word to `.harper/dictionary.txt` only when it is accepted terminology
   or a proper name, not merely to silence a useful warning.
6. Rerun the relevant linter and inspect the complete diff.

Do not edit generated exports or apply broad automated rewrites to academic
prose. Escalate ambiguous factual, conceptual, or citation changes to the
author.
