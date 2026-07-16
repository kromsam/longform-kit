#!/bin/sh
set -eu

ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
QUARTO_BIN=${QUARTO:-${LONGFORM_QUARTO:-quarto}}
PYTHON=${PYTHON:-python3}
STAGE=$(mktemp -d "${TMPDIR:-/tmp}/longform-template.XXXXXX")
trap 'rm -rf "$STAGE"' EXIT HUP INT TERM

fail() {
  printf 'template assertions: %s\n' "$*" >&2
  exit 1
}

(
  cd "$STAGE"
  "$QUARTO_BIN" use template --no-prompt "$ROOT"
)

for required in \
  bin/longform \
  document/_quarto.yml \
  document/_extensions/longform-kit/LICENSE \
  document/manuscript/01-introduction.md \
  share/templates/AGENTS.md.in; do
  [ -f "$STAGE/$required" ] || fail "missing generated file: $required"
done

for excluded in \
  CONTRIBUTING.md \
  SECURITY.md \
  tests \
  document/build \
  document/.quarto \
  document/index.tex \
  document/index.pdf; do
  [ ! -e "$STAGE/$excluded" ] || fail "copied excluded path: $excluded"
done

(
  cd "$STAGE"
  ./bin/longform setup
  ./bin/longform check
)

[ -f "$STAGE/AGENTS.md" ] || fail "setup did not create AGENTS.md"
[ -f "$STAGE/.gitignore" ] || fail "setup did not create .gitignore"
skills=$(find "$STAGE/.agents/skills" -name SKILL.md -type f | wc -l | tr -d ' ')
[ "$skills" -eq 4 ] || fail "setup installed $skills Agent Skills instead of 4"

cp "$ROOT/tests/fixtures/_quarto-latex-gfm-invalid.yml" \
  "$STAGE/document/_quarto-latex-gfm-invalid.yml"
if (
  cd "$STAGE"
  QUARTO_PROFILE=latex-gfm-invalid ./bin/longform check \
    >"$STAGE/gfm-error.log" 2>&1
); then
  fail "check accepted LaTeX-derived GFM with linked citations"
fi
if ! grep -q 'requires link-citations: false' "$STAGE/gfm-error.log"; then
  fail "LaTeX-derived GFM validation did not explain how to preserve citation text"
fi

cp "$ROOT/tests/fixtures/_quarto-latex-gfm.yml" \
  "$STAGE/document/_quarto-latex-gfm.yml"
(
  cd "$STAGE"
  QUARTO_PROFILE=latex-gfm ./bin/longform zettlr sync
  QUARTO_PROFILE=latex-gfm ./bin/longform build gfm
)
PYTHONDONTWRITEBYTECODE=1 "$PYTHON" "$ROOT/tests/assert_latex_gfm.py" \
  "$STAGE/document/build/longform-document.md" \
  "$STAGE/document/build/longform-document.tex"

cp "$ROOT/tests/fixtures/_quarto-fonts.yml" \
  "$STAGE/document/_quarto-fonts.yml"
(
  cd "$STAGE"
  PATH="$ROOT/tests/fixtures/font-present:$PATH" \
    QUARTO_PROFILE=fonts ./bin/longform doctor >/dev/null
)
if (
  cd "$STAGE"
  PATH="$ROOT/tests/fixtures/font-missing:$PATH" \
    QUARTO_PROFILE=fonts ./bin/longform doctor \
    >"$STAGE/font-error.log" 2>&1
); then
  fail "doctor accepted a fallback for a declared required font"
fi
if ! grep -q 'required font not available: Longform Test Serif' \
  "$STAGE/font-error.log"; then
  fail "doctor did not identify the unavailable required font"
fi

printf 'template assertions: clean starter setup passed\n'
