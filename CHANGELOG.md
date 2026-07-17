# Changelog

All notable changes to Longform Kit are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and releases use
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.3.0] - 2026-07-17

### Added

- A Markdown-only `document/` authoring boundary enforced by
  `bin/longform check`.
- The pinned Fancy Epigraphs v0.0.1 Quarto shortcode and its upstream licence.
- A project-local TeX cache for reliable PDF builds in sandboxed agent
  environments.

### Changed

- The repository root is now a standard Quarto book project. Configuration,
  profiles, generated Zettlr state, references, scripts, extensions, and
  `build/` no longer live under `document/`.
- PDF, DOCX, LaTeX, citeproc, TOCs, reference-DOCX styling, conditional content,
  and page breaks now use Quarto's native options.
- Combined GFM is rendered through a temporary standalone Quarto document so
  includes, shortcodes, format conditionals, and embedded images are resolved
  by Quarto and Pandoc.
- `bin/longform setup` now generates a project `LICENSE` from
  `share/templates/LICENSE.in` with the current year and the `_quarto.yml`
  `book.author` filled in. The kit's own MIT notice is excluded from generated
  projects so the licence belongs to the project's author.

### Removed

- The custom Longform Kit project type, custom output formats, Lua epigraph and
  page-break filters, manual Word TOC construction, manual citeproc invocation,
  custom LaTeX title/front-matter templates, and LaTeX-derived legacy GFM mode.

## [0.2.0] - 2026-07-16

### Added

- GFM builds can select Markdown or canonical LaTeX as their source with
  `longform.gfm-source`; Markdown remains the default, while LaTeX supports
  migration and frozen-export parity.
- Independent GFM and DOCX TOC depths, configurable Word TOC field switches,
  optional production-font checks, and opt-in DOCX compatibility controls for
  TOC, bibliography, and citation-note placement.
- DOCX epigraph controls for leading spacing, separators, flush quotations, and
  custom quotation and source styles.

### Changed

- LaTeX-derived GFM emits stable YAML metadata and requires citation links to
  be disabled for the citeproc round trip. YAML scalars are quoted when needed;
  an explicit legacy switch preserves historical plain-scalar bytes.
- DOCX chapter epigraphs now render their configured separator and apply the
  `First Paragraph` style to immediately following prose. The reference
  document no longer forces level-two headings onto a new page.

### Fixed

- The bundled Chicago style retains the expected `ed.` and `eds.` edition
  abbreviations with current Pandoc versions.
- DOCX projects can reproduce legacy epigraph, TOC, and bibliography spacing
  without project-specific output patches.

## [0.1.1] - 2026-07-16

### Fixed

- Cross-platform CI now uses the dedicated TinyTeX setup action and updates
  `tlmgr` before installing project packages.

## [0.1.0] - 2026-07-16

### Added

- Quarto book project type and starter for long-form Markdown projects.
- Reproducible PDF, binding PDF, DOCX, LaTeX, and GFM builds.
- Semantic front and chapter epigraphs, portable page breaks, and a generated
  bibliography location.
- Project-local Better CSL JSON and CSL citation workflow.
- Deterministic setup, validation, lint, build, doctor, and Zettlr commands.
- Provider-neutral `AGENTS.md` template and four Agent Skills.
- Tutorial, how-to, reference, and explanation documentation.

[Unreleased]: https://github.com/kromsam/longform-kit/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/kromsam/longform-kit/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/kromsam/longform-kit/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/kromsam/longform-kit/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/kromsam/longform-kit/releases/tag/v0.1.0
