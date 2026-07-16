#!/usr/bin/env python3
"""Assert the opt-in LaTeX-derived GFM contract in a staged project."""

from __future__ import annotations

from pathlib import Path
import json
import os
import re
import subprocess
import sys


def fail(message: str) -> None:
    raise AssertionError(message)


if len(sys.argv) != 3:
    print("usage: assert_latex_gfm.py OUTPUT.md CANONICAL.tex", file=sys.stderr)
    raise SystemExit(2)

gfm = Path(sys.argv[1])
latex = Path(sys.argv[2])
quarto = os.environ.get("QUARTO") or os.environ.get("LONGFORM_QUARTO") or "quarto"
for path in (gfm, latex):
    if not path.is_file() or path.stat().st_size == 0:
        fail(f"missing or empty LaTeX-mode output: {path}")

text = gfm.read_text(encoding="utf-8")
if not text.startswith("---\n"):
    fail("LaTeX-derived GFM does not begin with its YAML metadata header")

header_end = text.find("\n---\n", 4)
if header_end < 0:
    fail("LaTeX-derived GFM has an unterminated YAML metadata header")
header = text[: header_end + 5]
for expected in (
    'author:\n- Author Name\n- "Doe: Jane"\n- "001234"',
    "lang: en-GB",
    'subtitle: "Line one: \\"quoted\\" # evidence"',
    'title: "true"',
):
    if expected not in header:
        fail(f"LaTeX-derived GFM metadata is missing: {expected!r}")
if not re.search(r'^date: "\d{4}-\d{2}-\d{2}"$', header, re.MULTILINE):
    fail("LaTeX-derived GFM did not resolve the project date")

parsed = subprocess.run(
    [quarto, "pandoc", str(gfm), "--from=markdown", "--to=json"],
    check=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)
metadata = json.loads(parsed.stdout).get("meta", {})
if not all(key in metadata for key in ("author", "subtitle", "title")):
    fail("LaTeX-derived GFM metadata is not valid parseable YAML")

for expected in (
    "[Introduction](#introduction)",
    "Every long document begins with a first page.",
    "# Introduction",
    "# Conclusion",
    "# Bibliography",
):
    if expected not in text:
        fail(f"LaTeX-derived GFM is missing ordered document content: {expected!r}")
toc = text[header_end + 5 : text.find("# Introduction")]
if "[A section](#a-section)" in toc:
    fail("LaTeX-derived GFM ignored longform.gfm-toc-depth")
if "## A section" not in text:
    fail("GFM TOC-depth filtering removed the section from the document body")

note = re.search(r"^\[\^1\]:(.*(?:\n(?: {4}|\t).*)*)", text, re.MULTILINE)
if note is None:
    fail("LaTeX-derived GFM does not contain the citation footnote")
normalized_note = re.sub(r"\s+", " ", note.group(0))
for expected in (
    "Alex Example",
    "The Example Book",
    "2nd ed.",
    "Example Press",
    "1–2",
):
    if expected not in normalized_note:
        fail(f"LaTeX-derived GFM citation footnote is missing: {expected!r}")
if "\\citeproc{" in text or normalized_note == "[^1]: .":
    fail("LaTeX-derived GFM lost the linked citation's rendered note text")

latex_text = latex.read_text(encoding="utf-8")
if "\\citeproc{ref-exampleBook2024}" in latex_text:
    fail("the canonical LaTeX input for GFM still contains linked citation wrappers")

print("LaTeX-derived GFM assertions passed")
