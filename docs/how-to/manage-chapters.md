# Add And Reorder Chapters

The chapter list in `document/_quarto.yml` is authoritative for Quarto, Zettlr,
the GFM build, citation checks, and prose tooling.

## Add A Chapter

Create a Markdown file under `document/manuscript/` with one level-one heading:

```markdown
# Methods

Chapter text begins here.
```

Add its path under `book.chapters` in the intended reading order:

```yaml
book:
  chapters:
    - index.qmd
    - manuscript/01-introduction.md
    - manuscript/02-methods.md
    - manuscript/03-conclusion.md
    - references.md
```

Keep `index.qmd` first. Quarto books require that filename. Keep
`references.md` at the desired bibliography position, normally last.

## Reorder Or Rename A Chapter

Move or rename the source file, then update its path in `book.chapters`. Do not
edit `document/.ztr-directory` manually.

Synchronize and validate:

```sh
bin/longform zettlr sync
bin/longform check
```

The synchronization command derives Zettlr's file order from Quarto's resolved
project configuration.

Use `.unnumbered` on a chapter heading when it should not receive a chapter
number:

```markdown
# Preface {.unnumbered}
```
