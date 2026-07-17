#!/bin/sh
set -eu

ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON=${PYTHON:-python3}
QUARTO_BIN=${QUARTO:-${LONGFORM_QUARTO:-quarto}}

command -v "$PYTHON" >/dev/null 2>&1 || {
  printf 'tests: missing required command: %s\n' "$PYTHON" >&2
  exit 1
}
command -v "$QUARTO_BIN" >/dev/null 2>&1 || {
  printf 'tests: missing required command: %s\n' "$QUARTO_BIN" >&2
  exit 1
}

cd "$ROOT"

./bin/longform check
PYTHONDONTWRITEBYTECODE=1 "$PYTHON" tests/assert_project.py

for format in gfm docx latex; do
  ./bin/longform build "$format"
  PYTHONDONTWRITEBYTECODE=1 "$PYTHON" tests/assert_outputs.py "$format"
done

pdf_tools=true
for command in lualatex pdfinfo pdftotext pdffonts; do
  if ! command -v "$command" >/dev/null 2>&1; then
    pdf_tools=false
    printf 'tests: PDF verification unavailable; missing %s\n' "$command" >&2
  fi
done

if [ "$pdf_tools" = true ]; then
  ./bin/longform build pdf
  PYTHONDONTWRITEBYTECODE=1 "$PYTHON" tests/assert_outputs.py pdf
elif [ "${LONGFORM_REQUIRE_PDF:-0}" = 1 ]; then
  printf 'tests: PDF verification is required in this environment\n' >&2
  exit 1
else
  printf 'tests: skipped PDF build and verification\n'
fi

sh tests/assert_clone.sh

printf 'tests: all available Longform Kit checks passed\n'
