# Changelog

All notable changes to Longform Kit are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and releases use
[Semantic Versioning](https://semver.org/).

## [Unreleased]

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

[Unreleased]: https://github.com/kromsam/longform-kit/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/kromsam/longform-kit/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/kromsam/longform-kit/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/kromsam/longform-kit/releases/tag/v0.1.0
