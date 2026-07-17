# Work With AI Agents

Longform Kit uses open repository conventions rather than a provider-specific
configuration.

## Initialize Agent Files

Run:

```sh
bin/longform setup
```

The command creates `AGENTS.md` and installs reusable skills under
`.agents/skills/` when those paths do not already exist. Existing files are not
overwritten.

## Give Agents Deterministic Commands

Ask an agent to use the relevant skill and the repository CLI. Typical tasks
map to:

- `build-and-export` for validation and rendering.
- `verify-citations` for Zotero and citation-key work.
- `lint-prose` for Vale or Harper findings.
- `revise-academic-prose` for clarity and cohesion revisions.

The CLI is the common contract across agents:

```sh
bin/longform check
bin/longform lint
bin/longform build TARGET
```

Do not require an agent to reconstruct Quarto profiles or Pandoc arguments.

## Keep Integrations Optional

An agent may use a Zotero or web connector to verify bibliographic facts, but
the repository should not commit provider credentials or depend on a connector
to build. Prefer read-only access. Apply bibliographic corrections in Zotero and
allow Better BibTeX to update the checked-in export.

Review changes to Agent Skills, TypeScript project helpers, and Quarto
extensions as executable code before running them.
