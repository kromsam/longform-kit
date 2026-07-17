#!/bin/sh
set -eu

ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
QUARTO_BIN=${QUARTO:-${LONGFORM_QUARTO:-quarto}}
TEST_AREA=$(mktemp -d "${TMPDIR:-/tmp}/longform clone.XXXXXX")
STAGE="$TEST_AREA/project clone"
EXTERNAL_REFERENCES="$TEST_AREA/external reference inputs"
LIBRARY_DIRECTORY="$EXTERNAL_REFERENCES/Better BibTeX export"
LIBRARY="$LIBRARY_DIRECTORY/library.json"
ZOTERO_DATA="$EXTERNAL_REFERENCES/Zotero Data"
STYLE="$ZOTERO_DATA/styles/longform-test-note.csl"
DEPENDENT_STYLE="$ZOTERO_DATA/styles/longform-test-dependent.csl"
PARENT_STYLE="$ZOTERO_DATA/styles/hidden/renamed parent style.csl"
mkdir -p \
  "$STAGE/references" \
  "$LIBRARY_DIRECTORY" \
  "$ZOTERO_DATA/styles/hidden"
trap 'rm -rf "$TEST_AREA"' EXIT HUP INT TERM

fail() {
  printf 'clone assertions: %s\n' "$*" >&2
  exit 1
}

# Simulate a fresh clone without carrying configured reference links from the
# checkout that launched the test.
(
  cd "$ROOT"
  find . -maxdepth 1 -mindepth 1 \
    ! -name .git ! -name build ! -name .cache ! -name .quarto \
    ! -name references \
    -exec cp -R {} "$STAGE/" \;
)
(
  cd "$ROOT/references"
  find . -maxdepth 1 -mindepth 1 \
    ! -name library.json ! -name style.csl ! -name zotero-styles \
    ! -name .csl-parents \
    -exec cp -R {} "$STAGE/references/" \;
)

# A clone already carries the agent files, ignore rules, skills, and the Zettlr
# launcher; there is no template materialization step.
for required in \
  bin/longform \
  bin/longform-zettlr \
  _quarto.yml \
  index.md \
  document/.ztr-directory \
  AGENTS.md \
  .gitignore \
  .agents/skills \
  _extensions/epigraph/LICENSE \
  references/reference.docx \
  scripts/project.ts \
  tests/fixtures/references/library.json \
  tests/fixtures/references/longform-test-dependent.csl \
  tests/fixtures/references/longform-test-note.csl \
  tests/fixtures/references/longform-test-note-parent.csl \
  document/front-matter.md \
  document/metadata.yml \
  document/chapters.yml \
  document/manuscript/01-introduction.md; do
  [ -e "$STAGE/$required" ] || fail "clone is missing project file: $required"
done

for local_reference in library.json style.csl zotero-styles .csl-parents; do
  if [ -e "$STAGE/references/$local_reference" ] || \
    [ -L "$STAGE/references/$local_reference" ]; then
    fail "clone unexpectedly ships local reference input: references/$local_reference"
  fi
done

skills=$(find "$STAGE/.agents/skills" -name SKILL.md -type f | wc -l | tr -d ' ')
[ "$skills" -eq 4 ] || fail "clone carries $skills Agent Skills instead of 4"

touch "$ZOTERO_DATA/zotero.sqlite"
cp "$STAGE/tests/fixtures/references/library.json" "$LIBRARY"
cp "$STAGE/tests/fixtures/references/longform-test-note.csl" "$STYLE"
cp "$STAGE/tests/fixtures/references/longform-test-dependent.csl" \
  "$DEPENDENT_STYLE"
cp "$STAGE/tests/fixtures/references/longform-test-note-parent.csl" \
  "$PARENT_STYLE"

if grep -R -q '@exampleBook2024' "$STAGE/document"; then
  fail "starter manuscript unexpectedly contains the fixture citation"
fi
printf '\nThe clone test exercises a note citation [@exampleBook2024, 1-2].\n' \
  >>"$STAGE/document/manuscript/01-introduction.md"

rm "$STAGE/index.md"

(
  cd "$STAGE"
  ./bin/longform setup \
    --library "$LIBRARY_DIRECTORY" \
    --zotero-data-dir "$ZOTERO_DATA" \
    --style "Longform Test Note Style"
  ./bin/longform build gfm
)

for local_reference in library.json style.csl zotero-styles; do
  [ -L "$STAGE/references/$local_reference" ] || \
    fail "setup did not create a reference link: references/$local_reference"
done
[ "$STAGE/references/library.json" -ef "$LIBRARY" ] || \
  fail "library link does not resolve to the configured export"
[ "$STAGE/references/style.csl" -ef "$STYLE" ] || \
  fail "style title did not resolve to the installed CSL file"
[ "$STAGE/references/zotero-styles" -ef "$ZOTERO_DATA/styles" ] || \
  fail "Zotero styles link does not resolve to the configured styles directory"
grep -q 'Independent style citation:' \
  "$STAGE/build/longform-document.md" || \
  fail "GFM did not render a citation through the independent CSL style"

library_link=$(readlink "$STAGE/references/library.json")
style_link=$(readlink "$STAGE/references/style.csl")
styles_link=$(readlink "$STAGE/references/zotero-styles")
for style_selector in \
  "https://example.invalid/styles/longform-test-note" \
  "longform-test-note.csl"; do
  (
    cd "$STAGE"
    ./bin/longform setup \
      --library "$LIBRARY" \
      --zotero-data-dir "$ZOTERO_DATA" \
      --style "$style_selector" >/dev/null
  )
done
[ "$(readlink "$STAGE/references/library.json")" = "$library_link" ] || \
  fail "repeated setup or alternate style selector changed the library link"
[ "$(readlink "$STAGE/references/style.csl")" = "$style_link" ] || \
  fail "style title, ID, and filename did not resolve to the same link"
[ "$(readlink "$STAGE/references/zotero-styles")" = "$styles_link" ] || \
  fail "repeated setup or alternate style selector changed the styles link"

# A selector can match one installed style's filename and another style's
# title. Setup must reject that cross-field ambiguity instead of applying a
# precedence rule silently.
AMBIGUOUS_STYLE="$ZOTERO_DATA/styles/selector-collision.csl"
sed \
  -e 's#<csl:title><!\[CDATA\[Longform Test Note Style\]\]></csl:title>#<csl:title><![CDATA[longform-test-note.csl]]></csl:title>#' \
  -e 's#https://example.invalid/styles/longform-test-note#https://example.invalid/styles/selector-collision#g' \
  "$STAGE/tests/fixtures/references/longform-test-note.csl" \
  >"$AMBIGUOUS_STYLE"
if (
  cd "$STAGE"
  ./bin/longform setup \
    --library "$LIBRARY" \
    --zotero-data-dir "$ZOTERO_DATA" \
    --style "longform-test-note.csl" >"$TEST_AREA/ambiguous-style.log" 2>&1
); then
  fail "setup silently resolved an ambiguous CSL selector"
fi
grep -q 'CSL style name is ambiguous' "$TEST_AREA/ambiguous-style.log" || \
  fail "ambiguous CSL selector failure did not explain the problem"
rm "$AMBIGUOUS_STYLE"
[ "$(readlink "$STAGE/references/style.csl")" = "$style_link" ] || \
  fail "ambiguous style failure changed the style link"

# Better BibTeX commonly replaces an export when updating it. Replacing the
# external file must update the project immediately without recreating links.
sed 's/Example Press/Updated Example Press/' "$LIBRARY" >"$LIBRARY.next"
mv "$LIBRARY.next" "$LIBRARY"
grep -q 'Updated Example Press' "$STAGE/references/library.json" || \
  fail "library link did not follow a replaced auto-export"
printf '\n<!-- live style update -->\n' >>"$STYLE"
grep -q 'live style update' "$STAGE/references/style.csl" || \
  fail "style link did not expose an installed-style update"
cp "$STAGE/tests/fixtures/references/library.json" "$LIBRARY"

# A live installed style can be replaced independently of its stable symlink.
# Check must validate the current target rather than trusting setup's result.
cp "$STYLE" "$STYLE.valid"
cp "$STAGE/README.md" "$STYLE"
if (
  cd "$STAGE"
  ./bin/longform check >"$TEST_AREA/malformed-live-style.log" 2>&1
); then
  fail "check accepted a malformed live CSL style target"
fi
grep -q 'CSL style failed Pandoc validation' \
  "$TEST_AREA/malformed-live-style.log" || \
  fail "malformed live style failure did not explain the problem"
mv "$STYLE.valid" "$STYLE"

# Invalid reconfiguration must leave all previously valid links intact.
if (
  cd "$STAGE"
  ./bin/longform setup \
    --library "$LIBRARY" \
    --zotero-data-dir "$ZOTERO_DATA" \
    --style "Missing Test Style" >"$TEST_AREA/missing-style.log" 2>&1
); then
  fail "setup accepted a missing CSL style"
fi
[ -s "$TEST_AREA/missing-style.log" ] || \
  fail "missing CSL style failure did not explain the problem"
[ "$(readlink "$STAGE/references/library.json")" = "$library_link" ] || \
  fail "missing style failure changed the library link"
[ "$(readlink "$STAGE/references/style.csl")" = "$style_link" ] || \
  fail "missing style failure changed the style link"
[ "$(readlink "$STAGE/references/zotero-styles")" = "$styles_link" ] || \
  fail "missing style failure changed the Zotero styles link"

MALFORMED_LIBRARY="$EXTERNAL_REFERENCES/malformed library.json"
printf '{ not valid CSL JSON\n' >"$MALFORMED_LIBRARY"
if (
  cd "$STAGE"
  ./bin/longform setup \
    --library "$MALFORMED_LIBRARY" \
    --zotero-data-dir "$ZOTERO_DATA" \
    --style "Longform Test Note Style" >"$TEST_AREA/malformed-library.log" 2>&1
); then
  fail "setup accepted a malformed CSL JSON library"
fi
[ -s "$TEST_AREA/malformed-library.log" ] || \
  fail "malformed library failure did not explain the problem"
[ "$(readlink "$STAGE/references/library.json")" = "$library_link" ] || \
  fail "malformed library failure changed the library link"
[ "$(readlink "$STAGE/references/style.csl")" = "$style_link" ] || \
  fail "malformed library failure changed the style link"
[ "$(readlink "$STAGE/references/zotero-styles")" = "$styles_link" ] || \
  fail "malformed library failure changed the Zotero styles link"

# Pandoc only resolves local dependent parents for canonical URL-shaped IDs.
# Reject other URI forms during setup so an offline build never falls through
# to an HTTP request.
cp "$DEPENDENT_STYLE" "$DEPENDENT_STYLE.valid"
cp "$PARENT_STYLE" "$PARENT_STYLE.valid"
for parent_case in urn query bare_query bare_fragment; do
  case "$parent_case" in
    urn) parent_id='urn:uuid:12345678-1234-1234-1234-123456789abc' ;;
    query) parent_id='https://example.invalid/styles/longform-test-note-parent?version=1#revision' ;;
    bare_query) parent_id='https://example.invalid/styles/longform-test-note-parent?' ;;
    bare_fragment) parent_id='https://example.invalid/styles/longform-test-note-parent#' ;;
  esac
  sed \
    "s|https://example.invalid/styles/longform-test-note-parent|$parent_id|g" \
    "$DEPENDENT_STYLE.valid" >"$DEPENDENT_STYLE"
  sed \
    "s|https://example.invalid/styles/longform-test-note-parent|$parent_id|g" \
    "$PARENT_STYLE.valid" >"$PARENT_STYLE"
  if (
    cd "$STAGE"
    ./bin/longform setup \
      --library "$LIBRARY" \
      --zotero-data-dir "$ZOTERO_DATA" \
      --style "Longform Test Dependent Style" \
      >"$TEST_AREA/noncanonical-parent-$parent_case.log" 2>&1
  ); then
    fail "setup accepted a dependent parent ID that Pandoc cannot resolve locally"
  fi
  grep -q 'Dependent CSL parent cannot be resolved offline' \
    "$TEST_AREA/noncanonical-parent-$parent_case.log" || \
    fail "noncanonical parent failure did not explain the offline constraint"
done
mv "$DEPENDENT_STYLE.valid" "$DEPENDENT_STYLE"
mv "$PARENT_STYLE.valid" "$PARENT_STYLE"

# Zotero stores independent parents for dependent styles under styles/hidden.
# The parent URL deliberately cannot be fetched, so a successful render proves
# Pandoc resolved it through the linked local Zotero style directories.
(
  cd "$STAGE"
  ./bin/longform setup \
    --library "$LIBRARY" \
    --zotero-data-dir "$ZOTERO_DATA" \
    --style "Longform Test Dependent Style" >/dev/null
)
[ "$STAGE/references/style.csl" -ef "$DEPENDENT_STYLE" ] || \
  fail "setup did not select the dependent CSL style"
[ "$STAGE/references/.csl-parents/longform-test-note-parent.csl" -ef \
  "$PARENT_STYLE" ] || fail "dependent style parent ID did not resolve locally"

rm "$STAGE/references/.csl-parents/longform-test-note-parent.csl"
if (
  cd "$STAGE"
  ./bin/longform check >"$TEST_AREA/missing-parent-alias.log" 2>&1
); then
  fail "check accepted a dependent style with a missing parent alias"
fi
[ -s "$TEST_AREA/missing-parent-alias.log" ] || \
  fail "missing parent alias failure did not explain the problem"

(
  cd "$STAGE"
  ./bin/longform setup \
    --library "$LIBRARY" \
    --zotero-data-dir "$ZOTERO_DATA" \
    --style "Longform Test Dependent Style" >/dev/null
)
[ "$STAGE/references/.csl-parents/longform-test-note-parent.csl" -ef \
  "$PARENT_STYLE" ] || fail "setup did not restore the dependent style parent alias"

(
  cd "$STAGE"
  ./bin/longform check
)

[ "$(cat "$STAGE/index.md")" = '{{< include document/front-matter.md >}}' ] || \
  fail "setup did not restore the exact Quarto home-page adapter"

[ -f "$STAGE/AGENTS.md" ] || fail "clone is missing AGENTS.md"
[ -f "$STAGE/.gitignore" ] || fail "clone is missing .gitignore"

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
grep -q 'The Example Book' "$STAGE/build/longform-document.md" || \
  fail "GFM did not render a citation through the dependent CSL parent"
grep -q '2nd ed.' "$STAGE/build/longform-document.md" || \
  fail "dependent CSL parent did not control citation formatting"
if grep -q '{{< epigraph' "$STAGE/build/longform-document.md"; then
  fail "GFM did not expand the Fancy Epigraphs shortcode"
fi
grep -q 'Included GFM resource text.' "$STAGE/build/longform-document.md" || \
  fail "GFM did not resolve a project-relative include"
grep -q 'longform-document_files/resources/example.svg' \
  "$STAGE/build/longform-document.md" || fail "GFM did not rewrite extracted media"
[ -s "$STAGE/build/longform-document_files/resources/example.svg" ] || \
  fail "GFM did not promote extracted media beside the output"
if find "$STAGE/document" -type f ! -name '*.md' ! -name 'metadata.yml' ! -name 'chapters.yml' ! -name '.ztr-directory' | grep -q .; then
  fail "clone put an unexpected non-Markdown file under document/"
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
  fail "clone gitignore does not exclude the project-local TeX cache"
grep -q '^/\*_files/$' "$STAGE/.gitignore" || \
  fail "clone gitignore does not exclude Quarto support directories"

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

printf 'clone assertions: clean clone setup passed\n'
