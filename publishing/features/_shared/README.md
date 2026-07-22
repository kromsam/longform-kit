# Optional-feature support code

`_shared` contains internal Python helpers used by bundled optional features.
It is not an activatable feature, has no Quarto registration, and has no
runtime effect by itself. Its OOXML helpers provide namespace handling,
package validation, deterministic ZIP preservation, output discovery through
`QUARTO_PROJECT_OUTPUT_FILES`, and atomic replacement.

This infrastructure is part of Longform Kit and is licensed under the MIT
terms in the repository `LICENSE`.
