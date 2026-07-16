#!/bin/sh
set -eu

ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
QUARTO_BIN=${QUARTO:-${LONGFORM_QUARTO:-quarto}}
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

printf 'template assertions: clean starter setup passed\n'
