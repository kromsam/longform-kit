---
name: lint-prose
description: Run and interpret prose linting for a Longform Kit manuscript with Vale or Harper. Use for copyediting, spelling and style checks, pre-submission cleanup, dictionary maintenance, or resolving prose-linter findings without damaging academic meaning or Markdown.
---

# Lint Prose

## Workflow

1. Read `AGENTS.md` and any project editorial style guide.
2. Run `bin/longform lint`. The command uses Vale and Harper when available and
   reports when neither is installed.
3. Triage findings in context. Linters provide evidence, not editorial
   authority.
4. Make narrow source edits under `document/`; preserve quotations, citation
   keys, language attributes, Quarto shortcodes, conditional Divs, and
   technical terminology.
5. Add a word to a project dictionary only when it is genuinely accepted
   terminology or a proper name, not merely to silence a useful warning.
6. Rerun the linter on the changed material and inspect the diff.

Do not edit generated exports or apply broad automated rewrites to academic
prose. Escalate ambiguous factual, conceptual, or citation changes to the author.
