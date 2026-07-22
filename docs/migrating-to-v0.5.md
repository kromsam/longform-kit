# Migrate To v0.5

Longform Kit v0.5 reorganizes the repository around four clear concerns:
writing, materials, style policy, and publishing implementation. The release
changes paths and commands. It deliberately provides no compatibility aliases,
so stale references fail visibly instead of preserving two competing layouts.

## Path Changes

| Before v0.5 | v0.5 and later |
| --- | --- |
| `document/metadata.yml` | `writing/manuscript/metadata.yml` |
| `document/chapters.yml` | `writing/manuscript/chapters.yml` |
| `document/front-matter.md` | `writing/manuscript/front-matter.md` |
| `document/manuscript/` | `writing/manuscript/chapters/` |
| `document/references.md` | `writing/manuscript/bibliography.md` |
| `document/.ztr-directory` | `writing/.ztr-directory` |
| `scripts/longform.ts` | `publishing/longform.ts` |
| `filters/longform-front-matter.lua` | `publishing/filters/front-matter.lua` |
| `references/reference.docx` | `publishing/docx/reference.docx` |
| `scripts/sanitize-docx.lua` | `publishing/docx/sanitize.lua` |
| `tests/` | `publishing/tests/` |
| `build/` | `output/` |

The release also adds:

- `writing/drafts/`, `writing/notes/`, and `writing/planning/` for writing that
  is not an active rendering input;
- `materials/` for figures, attachments, feedback, and other document inputs;
- `style/editorial.md` and `style/typography.md` for document policy.

Root `README.md`, `docs/`, `_quarto.yml`, `_quarto-custom.yml`, and `index.md`
remain at the project root. `_quarto-custom.yml` remains the committed custom
profile; there is no profile-name migration.

## Adopt The Release In A Tracked Downstream

Create a branch and merge the release tag normally so future releases retain a
shared merge base:

```sh
git fetch upstream --tags
git switch main
git pull --ff-only origin main
git switch -c chore/sync-longform-v0.5.0
git merge --no-ff --no-edit v0.5.0
```

Resolve generic publishing files in favour of the release while preserving
document-owned writing, materials, style policy, custom profile, archives, and
Harper vocabulary. Do not pre-move upstream-owned files before the merge; that
turns upstream renames into rename-versus-edit conflicts.

After the upstream merge is recorded, place downstream-only material in the
new ownership boundaries:

- active manuscript prose under `writing/manuscript/`;
- unfinished writing under `writing/drafts/`, `writing/notes/`, or
  `writing/planning/`;
- figures, attachments, feedback, and source material under `materials/`;
- editorial and typographic policy under `style/`;
- executable document features under `publishing/features/<feature>/`;
- historical records under the downstream's archive structure.

Keep frozen archives byte-for-byte unless their preservation policy explicitly
allows internal changes.

## Update Project References

Search committed files for old commands and paths:

```sh
rg -n 'scripts/longform|tests/test_build|document/|references/reference|build/'
```

Update:

- `_quarto.yml` metadata, chapter, output, filter, and reference-DOCX paths;
- `writing/manuscript/chapters.yml` chapter entries;
- downstream profiles, filters, templates, post-processors, tests, and CI;
- README, AGENTS, Agent Skills, lint commands, ignore rules, and licensing
  ownership lists;
- project-root media references when material moved into `materials/`.

Use the new public commands everywhere:

```sh
quarto run publishing/longform.ts zettlr
python3 publishing/tests/test_build.py
quarto run publishing/longform.ts build
```

Do not add wrapper scripts, duplicate files, or symlinks at the old locations.
Documentation may mention old paths only when explaining this migration.

## Preserve Local State

Do not commit or rewrite another user's `_quarto.yml.local`. Its
`bibliography` and `csl` values remain absolute machine-local paths and do not
change merely because the repository layout changed. Existing ignored exports
inside the retired `references/` directory may remain there during migration;
new setups should prefer a stable location outside the repository. Any later
move of local exports and update to `_quarto.yml.local` is a deliberate action
for that contributor, not part of the tracked migration.

Both `build/` and the old `document/.ztr-directory` may remain locally after
the merge. They are retired generated state, not v0.5 outputs. Keep them
ignored until each contributor has verified the new build; remove them only as
an explicit local cleanup.

## Verify The Migration

Confirm local citation inputs are readable, then run:

```sh
quarto run publishing/longform.ts zettlr
python3 publishing/tests/test_build.py
quarto run publishing/longform.ts build
git merge-base --is-ancestor v0.5.0 HEAD
```

The build must create non-empty PDF, two-up PDF, DOCX, and combined GFM files
under `output/`. Inspect both PDFs and the DOCX when the downstream has custom
rendering. Confirm `writing/.ztr-directory` is ignored, no generated output is
tracked, and no old path remains outside this guide.
