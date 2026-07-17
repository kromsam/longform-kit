#!/bin/sh
set -eu

ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON=${PYTHON:-python3}
QUARTO_BIN=${QUARTO:-${LONGFORM_QUARTO:-quarto}}

copy_project() {
  source=$1
  destination=$2
  mkdir -p "$destination/references"
  (
    cd "$source"
    find . -maxdepth 1 -mindepth 1 \
      ! -name .git ! -name build ! -name .cache ! -name .quarto \
      ! -name references \
      -exec cp -R {} "$destination/" \;
  )
  if [ -d "$source/references" ]; then
    (
      cd "$source/references"
      find . -maxdepth 1 -mindepth 1 \
        ! -name library.json ! -name style.csl ! -name zotero-styles \
        ! -name .csl-parents \
        -exec cp -R {} "$destination/references/" \;
    )
  fi
}

# The active checkout may contain author-specific reference links. Run the
# entire suite in a disposable clone and never copy those links into it.
if [ "${LONGFORM_TEST_STAGED:-0}" != 1 ]; then
  TEST_AREA=$(mktemp -d "${TMPDIR:-/tmp}/longform tests.XXXXXX")
  trap 'rm -rf "$TEST_AREA"' EXIT HUP INT TERM
  STAGED_PROJECT="$TEST_AREA/project clone"
  EXTERNAL_REFERENCES="$TEST_AREA/external references"
  copy_project "$ROOT" "$STAGED_PROJECT"
  (
    cd "$STAGED_PROJECT"
    LONGFORM_TEST_STAGED=1 \
      LONGFORM_TEST_EXTERNAL_REFERENCES="$EXTERNAL_REFERENCES" \
      ./tests/run.sh
  )
  exit
fi

command -v "$PYTHON" >/dev/null 2>&1 || {
  printf 'tests: missing required command: %s\n' "$PYTHON" >&2
  exit 1
}
command -v "$QUARTO_BIN" >/dev/null 2>&1 || {
  printf 'tests: missing required command: %s\n' "$QUARTO_BIN" >&2
  exit 1
}

cd "$ROOT"

# Exercise first-run setup while this staged checkout still has neither local
# reference links nor the citation that the format assertions add below.
sh tests/assert_clone.sh

EXTERNAL_REFERENCES=${LONGFORM_TEST_EXTERNAL_REFERENCES:?missing staged reference directory}
LIBRARY="$EXTERNAL_REFERENCES/library export.json"
ZOTERO_DATA="$EXTERNAL_REFERENCES/Zotero Data"
STYLE="$ZOTERO_DATA/styles/longform-test-note.csl"
DEPENDENT_STYLE="$ZOTERO_DATA/styles/longform-test-dependent.csl"
PARENT_STYLE="$ZOTERO_DATA/styles/hidden/renamed parent style.csl"
mkdir -p "$ZOTERO_DATA/styles/hidden"
touch "$ZOTERO_DATA/zotero.sqlite"
cp tests/fixtures/references/library.json "$LIBRARY"
cp tests/fixtures/references/longform-test-note.csl "$STYLE"
cp tests/fixtures/references/longform-test-dependent.csl "$DEPENDENT_STYLE"
cp tests/fixtures/references/longform-test-note-parent.csl "$PARENT_STYLE"

if grep -R -q '@exampleBook2024' document; then
  printf 'tests: starter manuscript unexpectedly contains the fixture citation\n' >&2
  exit 1
fi
printf '\nThe staged test project exercises a note citation [@exampleBook2024, 1-2].\n' \
  >>document/manuscript/01-introduction.md

./bin/longform setup \
  --library "$LIBRARY" \
  --zotero-data-dir "$ZOTERO_DATA" \
  --style "Longform Test Dependent Style"

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

printf 'tests: all available Longform Kit checks passed\n'
