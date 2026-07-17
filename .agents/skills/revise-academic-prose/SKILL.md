---
name: revise-academic-prose
description: Revise academic prose in a Longform Kit manuscript for clarity, cohesion, emphasis, concision, and grace using Williams and Bizup-inspired principles. Use for paragraph or chapter revision while preserving claims, citations, quotations, terminology, and authorial voice.
---

# Revise Academic Prose

Read `references/williams-bizup.md` before revising. Also read the project's
editorial style guide and the surrounding section.

## Workflow

1. State the passage's conceptual task and preserve it throughout the revision.
2. Identify the important actors and actions. Prefer them as grammatical
   subjects and verbs when that improves clarity.
3. Put familiar context before new or complex information, and place material
   deserving emphasis near sentence endings.
4. Check topic continuity across sentences and the logical progression between
   paragraphs.
5. Remove avoidable nominalizations, throat-clearing, repetition, and abstract
   metadiscourse without flattening necessary qualification.
6. Preserve quotation wording, citation keys and locators, factual claims,
   specialist terms, and meaningful ambiguity.
7. Compare the complete diff with the source. Run the configured Vale or Harper
   checks when relevant. Run `quarto run scripts/longform.ts build` only when
   the revision changes structural Markdown or citation rendering.

Do not add evidence, strengthen claims, resolve theoretical tensions, or invent
transitions that the source cannot support. Flag those issues separately.
