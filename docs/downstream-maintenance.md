# Maintain a Tracked Downstream

A document can remain an independent repository while retaining Longform Kit's
Git ancestry. That shared ancestry makes later upstream releases ordinary Git
merges instead of repeated file-copy migrations.

GitHub's **Use this template** action is useful for a one-time snapshot, but a
repository created from a template starts with a single new commit. Its history
is [unrelated to the template's history][template-history]. A literal fork
retains history. However, [all forks of a public repository are
public][fork-visibility]. For a private or independently governed document that
should receive updates, clone Longform Kit and reassign the remotes instead.

[template-history]: https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template
[fork-visibility]: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/about-permissions-and-visibility-of-forks

## Start with Shared Ancestry

Create an empty destination repository without a README or initial commit, then
clone Longform Kit and assign each remote one role:

```sh
git clone git@github.com:kromsam/longform-kit.git my-document
cd my-document
git remote rename origin upstream
git remote add origin git@github.com:OWNER/MY-DOCUMENT.git
git push -u origin main
```

`origin` belongs to the document. It contains the manuscript, document history,
and collaboration branches. `upstream` points to Longform Kit and is the source
of generic fixes and version tags. Confirm that distinction before every push:

```sh
git remote -v
```

If a document already has an unrelated history, preserve both histories with a
normal two-parent adoption merge using `--allow-unrelated-histories`. Archive
and push the document's pre-adoption tip first. Do not squash, rebase, or force
push the adoption:

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

After validating the migration branch, the document's `main` can fast-forward
to it. If branch protection requires a pull request, use a merge commit so the
two parent histories remain reachable.

## Respect Ownership Boundaries

The initial clone contains starter content. Once a document is initialized,
resolve future upstream merges according to ownership rather than accepting one
side for the entire tree.

| Ownership | Paths | Merge rule |
| --- | --- | --- |
| Upstream | `scripts/longform.ts`, `tests/`, root `index.md`, `references/reference.docx`, `.agents/skills/`, generic documentation, and generic lint rules | Prefer the released upstream version. Contribute reusable changes to Longform Kit first. |
| Document | `document/`, `resources/`, notes, drafts, feedback, archives, submissions, and committed document profiles such as `_quarto-thesis.yml` | Preserve the document version. Upstream starter-prose changes do not replace manuscript content. |
| Local only | `_quarto.yml.local`, `document/.ztr-directory`, `build/`, and citation exports | Keep ignored and out of every merge and commit. |
| Merge seams | `_quarto.yml`, `.github/workflows/ci.yml`, `.gitignore`, `README.md`, `AGENTS.md`, `LICENSE`, and `.harper/dictionary.txt` | Reconcile deliberately. Keep `_quarto.yml` aligned except for the document's default-profile declaration, and retain document identity and vocabulary while incorporating compatible upstream machinery and policy. |

`document/metadata.yml` and `document/chapters.yml` are document-owned even
though Longform Kit supplies starter versions. Keep citation metadata in Zotero
and machine-local absolute `bibliography` and `csl` paths in the ignored
`_quarto.yml.local` file. Keep citation exports outside the repository or at
the ignored paths `references/library.json` and `references/style.csl`.

## Layer Document Configuration

Keep committed document-specific rendering changes in a named Quarto profile
instead of repeatedly editing the shared settings. For a thesis, add only the
profile activation to `_quarto.yml`:

```yaml
profile:
  default: thesis
```

Then put the document-owned overrides in `_quarto-thesis.yml`. Quarto
deep-merges objects and combines arrays, so a profile can add filters, header
includes, template partials, and post-render hooks while retaining the shared
Longform Kit configuration. Keep the document's output filename with its other
identity metadata in `document/metadata.yml`. Machine-specific bibliography and
CSL paths still belong only in ignored `_quarto.yml.local`.

## Merge a Released Version

Sync from published release tags rather than an arbitrary moving branch:

```sh
git fetch upstream --tags
git switch main
git pull --ff-only origin main
git switch -c chore/sync-longform-vX.Y.Z
git merge --no-ff --no-edit vX.Y.Z
```

Resolve conflicts using the ownership table. Confirm that the ignored
`_quarto.yml.local` points to readable citation inputs, then regenerate optional
editor state and verify every output:

```sh
quarto run scripts/longform.ts zettlr
python3 tests/test_build.py
quarto run scripts/longform.ts build
vale sync
vale document
harper-cli lint -d british -u .harper/dictionary.txt document/*.md document/manuscript/*.md
markdownlint-cli2 README.md "docs/**/*.md" "document/**/*.md"
git merge-base --is-ancestor vX.Y.Z HEAD
```

Run whichever linters are installed and inspect both rendered PDFs and the DOCX
when a release changes PDF styling or pagination. Complete the merge commit,
then merge or fast-forward the sync branch into `main`. If branch protection
requires a pull request, choose **Create a merge commit**. Squash- or
rebase-merging the sync branch would discard the ancestry that makes later
updates manageable.

## Contribute Generic Fixes Upstream First

Do not develop reusable build fixes on top of a manuscript branch. A clean
worktree rooted at `upstream/main` prevents document-only files and history from
leaking into the contribution:

```sh
git fetch upstream
git worktree add ../longform-kit-fix -b fix/short-description upstream/main
cd ../longform-kit-fix
```

Implement and test the generic change there, commit it, and contribute that
branch to Longform Kit. With upstream write access, push the contribution branch
to `upstream`:

```sh
git push -u upstream fix/short-description
```

Without upstream write access, add a separate fork remote and push there. Open
the pull request against Longform Kit, never against the document's `origin`:

```sh
git remote add fork git@github.com:ACCOUNT/longform-kit.git
git push -u fork fix/short-description
```

After the fix is merged and released upstream, remove the worktree, fetch the
new tag in the document repository, and follow the release-merge workflow
above. This keeps the reusable implementation in one history and leaves the
document with only its configuration and content.
