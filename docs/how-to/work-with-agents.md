# Work With AI Agents

Longform Kit uses open repository conventions rather than a provider-specific
configuration.

## Initialize Agent Files

Run:

```sh
bin/longform setup
```

`AGENTS.md` and the reusable skills under `.agents/skills/` already ship in the
repository. Setup links the checkout's external Better CSL JSON export and
installed Zotero styles, then regenerates the project adapters. The
machine-local citation links are not committed.

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
allow Better BibTeX to update the linked external export. Do not edit generated
CSL JSON or installed Zotero styles through their project symlinks.

An agent or CI runner on a fresh checkout must run `bin/longform setup` with
that machine's Better CSL JSON export location, Zotero data directory, and
style selection before checking or building. The export location may be the
exact file or a directory containing `library.json`; it is not the Zotero data
directory or `zotero.sqlite`.

Review changes to Agent Skills, TypeScript project helpers, and Quarto
extensions as executable code before running them.
