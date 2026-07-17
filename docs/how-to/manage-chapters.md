# Add And Reorder Chapters

The chapter list in root `_quarto.yml` is authoritative for Quarto, Zettlr, GFM,
citation checks, and prose tooling.

## Add A Chapter

Create `document/manuscript/02-methods.md` with a level-one heading, then add its
root-relative path in reading order:

```yaml
book:
  chapters:
    - index.md
    - document/manuscript/01-introduction.md
    - document/manuscript/02-methods.md
    - document/manuscript/03-conclusion.md
    - document/references.md
```

Keep generated `index.md` first. Edit `document/front-matter.md` rather than the
adapter. Keep `document/references.md` at the intended bibliography position,
normally last.

## Reorder Or Rename A Chapter

Move or rename the `.md` source, update `book.chapters`, then run:

```sh
bin/longform zettlr sync
bin/longform check
```

Do not edit `.ztr-directory` by hand. Use `.unnumbered` on a chapter heading
when it should not receive a number:

```markdown
# Preface {.unnumbered}
```
