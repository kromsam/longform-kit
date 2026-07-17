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
  _quarto.yml \
  index.md \
  _extensions/epigraph/LICENSE \
  references/library.json \
  scripts/project.ts \
  document/front-matter.md \
  document/metadata.yml \
  document/chapters.yml \
  document/manuscript/01-introduction.md \
  share/templates/AGENTS.md.in; do
  [ -f "$STAGE/$required" ] || fail "missing generated file: $required"
done

for excluded in \
  tests \
  build \
  .cache \
  .quarto \
  index.tex \
  index.pdf; do
  [ ! -e "$STAGE/$excluded" ] || fail "copied excluded path: $excluded"
done

rm "$STAGE/index.md"

(
  cd "$STAGE"
  ./bin/longform setup
  ./bin/longform check
)

[ "$(cat "$STAGE/index.md")" = '{{< include document/front-matter.md >}}' ] || \
  fail "setup did not restore the exact Quarto home-page adapter"

[ -f "$STAGE/AGENTS.md" ] || fail "setup did not create AGENTS.md"
[ -f "$STAGE/.gitignore" ] || fail "setup did not create .gitignore"
skills=$(find "$STAGE/.agents/skills" -name SKILL.md -type f | wc -l | tr -d ' ')
[ "$skills" -eq 4 ] || fail "setup installed $skills Agent Skills instead of 4"

(
  mkdir -p "$STAGE/resources"
  printf '%s\n' 'Included GFM resource text.' >"$STAGE/resources/gfm-include.txt"
  printf '%s\n' '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"><rect width="1" height="1"/></svg>' \
    >"$STAGE/resources/example.svg"
  printf '%s\n' \
    '' \
    '{{< include /resources/gfm-include.txt >}}' \
    '' \
    '::: {.content-visible when-format="gfm"}' \
    '![Example media.](/resources/example.svg)' \
    ':::' \
    >>"$STAGE/document/manuscript/02-conclusion.md"
  cd "$STAGE"
  ./bin/longform build gfm
)
[ -s "$STAGE/build/longform-document.md" ] || fail "GFM build is missing"
grep -q 'Every long document begins with a first page.' \
  "$STAGE/build/longform-document.md" || fail "GFM omitted the epigraph"
if grep -q '{{< epigraph' "$STAGE/build/longform-document.md"; then
  fail "GFM did not expand the Fancy Epigraphs shortcode"
fi
grep -q 'Included GFM resource text.' "$STAGE/build/longform-document.md" || \
  fail "GFM did not resolve a project-relative include"
grep -q 'longform-document_files/resources/example.svg' \
  "$STAGE/build/longform-document.md" || fail "GFM did not rewrite extracted media"
[ -s "$STAGE/build/longform-document_files/resources/example.svg" ] || \
  fail "GFM did not promote extracted media beside the output"
if find "$STAGE/document" -type f ! -name '*.md' ! -name 'metadata.yml' ! -name 'chapters.yml' | grep -q .; then
  fail "generated project put an unexpected non-Markdown file under document/"
fi

cp "$ROOT/tests/fixtures/_quarto-fonts.yml" \
  "$STAGE/_quarto-fonts.yml"
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

grep -q '^/.cache/$' "$STAGE/.gitignore" || \
  fail "generated gitignore does not exclude the project-local TeX cache"
grep -q '^/\*_files/$' "$STAGE/.gitignore" || \
  fail "generated gitignore does not exclude Quarto support directories"

(
  cd "$STAGE"
  HOME="$STAGE/home" ./bin/longform zettlr install >"$STAGE/zettlr-install.log"
)
grep -q '^Add this Zettlr custom export command: longform-zettlr$' \
  "$STAGE/zettlr-install.log" || fail "installer printed an invalid Zettlr command"
if grep -Fq '$1' "$STAGE/zettlr-install.log"; then
  fail "installer asks users to add a positional argument that Zettlr supplies"
fi
grep -Fq '"$directory/bin/longform" build all' \
  "$STAGE/home/.local/bin/longform-zettlr" || \
  fail "Zettlr launcher does not find the root CLI"

printf 'template assertions: clean starter setup passed\n'
