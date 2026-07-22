# Maintain A Tracked Downstream

A document can remain an independent repository while retaining Longform Kit's
Git ancestry. Shared ancestry makes later releases ordinary Git merges rather
than repeated file-copy migrations.

GitHub's **Use this template** action creates a one-time snapshot with unrelated
history. A literal fork retains history, but public-repository forks are public.
For a private or independently governed document that should receive updates,
clone Longform Kit and reassign the remotes instead.

## Start With Shared Ancestry

Create an empty destination repository without a README or initial commit, then
clone Longform Kit and give each remote one role:

```sh
git clone git@github.com:kromsam/longform-kit.git my-document
cd my-document
git remote rename origin upstream
git remote add origin git@github.com:OWNER/MY-DOCUMENT.git
git push -u origin main
```

`origin` belongs to the document. `upstream` points to Longform Kit and supplies
generic fixes and release tags. Confirm that distinction before every push:

```sh
git remote -v
```

If a document already has unrelated history, archive and push its current tip,
then retain both histories with one normal adoption merge. Do not squash,
rebase, or force-push the adoption:

```sh
git switch main
git pull --ff-only origin main
git branch archive/pre-longform-adoption
git push origin archive/pre-longform-adoption
git remote add upstream git@github.com:kromsam/longform-kit.git
git fetch upstream --tags
git switch -c migration/adopt-longform-vX.Y.Z vX.Y.Z
git merge --no-ff --allow-unrelated-histories archive/pre-longform-adoption
```

After verification, merge that branch with a merge commit so both parent
histories remain reachable.

## Respect Ownership Boundaries

The starter contains generic infrastructure and sample document content. Once
a document is initialized, resolve later upstream merges by ownership rather
than accepting one side across the tree.

| Ownership | Paths | Merge rule |
| --- | --- | --- |
| Upstream | `publishing/longform.ts`, `publishing/filters/`, `publishing/docx/`, `publishing/tests/`, root `index.md`, `.agents/skills/`, generic documentation, and generic lint rules | Prefer the released upstream version. Contribute reusable changes to Longform Kit first. |
| Document | `writing/`, `materials/`, `style/`, downstream `publishing/features/`, archives, submissions, `.harper/dictionary.txt`, and `_quarto-custom.yml` | Preserve the document version. Upstream starter prose and policy do not replace document content. |
| Local only | `_quarto.yml.local`, `writing/.ztr-directory`, `output/`, citation exports, and tool caches | Keep ignored and out of every merge and commit. |
| Merge seams | `_quarto.yml`, `.github/workflows/ci.yml`, `.gitignore`, `README.md`, `AGENTS.md`, and `LICENSE` | Reconcile deliberately. Incorporate compatible upstream machinery while preserving document ownership and licensing. |

`writing/manuscript/metadata.yml` and `writing/manuscript/chapters.yml` are
document-owned even though Longform Kit supplies starter versions. Change
bibliographic metadata in Zotero, not in its generated JSON export. Keep the
absolute `bibliography` and `csl` paths in ignored `_quarto.yml.local`.

The Harper dictionary is also document-owned. Upstream starts it empty; a
downstream should populate it only with accepted manuscript vocabulary.

## Layer Document Configuration

Longform Kit activates the tracked custom profile from `_quarto.yml`:

```yaml
profile:
  default: custom
```

Put document-owned rendering overrides in `_quarto-custom.yml` instead of
repeatedly editing shared settings. Quarto deep-merges objects and combines
arrays, so the profile can add filters, header includes, template partials,
and post-render hooks while retaining shared Longform Kit configuration.

Keep the document's output filename with its other identity metadata in
`writing/manuscript/metadata.yml`. Machine-specific bibliography and CSL paths
still belong only in `_quarto.yml.local`.

## Merge A Released Version

Sync from a published release tag rather than an arbitrary moving branch:

```sh
git fetch upstream --tags
git switch main
git pull --ff-only origin main
git switch -c chore/sync-longform-vX.Y.Z
git merge --no-ff --no-edit vX.Y.Z
```

Resolve conflicts using the ownership table. Confirm that the ignored local
configuration points to readable citation inputs, then regenerate optional
editor state and verify every output:

```sh
quarto run publishing/longform.ts zettlr
python3 publishing/tests/test_build.py
quarto run publishing/longform.ts build
vale sync
vale writing/manuscript
harper-cli lint -d british -u .harper/dictionary.txt \
  writing/manuscript/*.md writing/manuscript/chapters/*.md
markdownlint-cli2 README.md "docs/**/*.md" "writing/**/*.md" "style/**/*.md"
git merge-base --is-ancestor vX.Y.Z HEAD
```

Inspect both PDFs and the DOCX when a release changes rendering or pagination.
Merge the sync branch with a merge commit. Squash- or rebase-merging it would
discard the ancestry that makes later updates manageable.

Version 0.5 introduced a breaking directory reorganisation. Follow
[Migrate to v0.5](migrating-to-v0.5.md) while adopting that release; it has no
old-path aliases.

## Contribute Generic Fixes Upstream First

Do not develop reusable build fixes on top of a manuscript branch. A clean
worktree rooted at `upstream/main` prevents document-only files and history from
leaking into the contribution:

```sh
git fetch upstream
git worktree add ../longform-kit-fix -b fix/short-description upstream/main
cd ../longform-kit-fix
```

Implement and test the generic change there, then push it to Longform Kit when
you have write access:

```sh
git push -u upstream fix/short-description
```

Without upstream access, push the branch to a separate fork and open the pull
request against Longform Kit, not the document's `origin`:

```sh
git remote add fork git@github.com:ACCOUNT/longform-kit.git
git push -u fork fix/short-description
```

After the fix is merged and released upstream, remove the temporary worktree,
fetch the new tag in the document repository, and follow the release-merge
workflow above. The reusable implementation then remains in one upstream
history, while the document contains only its configuration and content.
