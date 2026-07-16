#!/usr/bin/env python3
"""Assert the public project manifest, Zettlr adapter, and citations agree."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = ROOT / "document"
QUARTO = os.environ.get("QUARTO") or os.environ.get("LONGFORM_QUARTO") or "quarto"


def fail(message: str) -> None:
    raise AssertionError(message)


def run(*args: str) -> str:
    result = subprocess.run(
        [QUARTO, *args],
        cwd=DOCUMENT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout


def citation_ids(value: Any) -> set[str]:
    found: set[str] = set()

    def visit(node: Any) -> None:
        if isinstance(node, list):
            for child in node:
                visit(child)
        elif isinstance(node, dict):
            if node.get("t") == "Cite":
                citations = node.get("c", [[], []])[0]
                for citation in citations:
                    identifier = citation.get("citationId")
                    if isinstance(identifier, str):
                        found.add(identifier)
            for child in node.values():
                visit(child)

    visit(value)
    return found


inspection = json.loads(run("inspect"))
config = inspection.get("config", {})
project = config.get("project", {})
book = config.get("book", {})
chapters = project.get("render", [])

if not chapters or not all(isinstance(path, str) for path in chapters):
    fail("Quarto did not resolve an ordered list of source files")

for relative in chapters:
    path = (DOCUMENT / relative).resolve()
    try:
        path.relative_to(DOCUMENT.resolve())
    except ValueError:
        fail(f"source path escapes document root: {relative}")
    if not path.is_file():
        fail(f"source file does not exist: {relative}")

csl = config.get("csl")
if not isinstance(csl, str) or not csl:
    fail("_quarto.yml must declare one project-local CSL file")
if not (DOCUMENT / csl).is_file():
    fail(f"CSL file does not exist: {csl}")

expected_zettlr = {
    "sorting": "name-up",
    "project": {
        "title": book.get("title", "Longform document"),
        "profiles": [],
        "files": chapters,
        "cslStyle": csl,
        "templates": {"tex": "", "html": ""},
    },
    "icon": None,
    "color": None,
}
zettlr = json.loads((DOCUMENT / ".ztr-directory").read_text(encoding="utf-8"))
if zettlr != expected_zettlr:
    fail("document/.ztr-directory does not exactly match resolved Quarto configuration")

bibliographies = config.get("bibliography")
if isinstance(bibliographies, str):
    bibliographies = [bibliographies]
if not isinstance(bibliographies, list) or len(bibliographies) != 1:
    fail("Longform Kit v1 requires exactly one bibliography")

bibliography_path = DOCUMENT / bibliographies[0]
entries = json.loads(bibliography_path.read_text(encoding="utf-8"))
if not isinstance(entries, list):
    fail("bibliography must be a CSL JSON array")

available: set[str] = set()
for entry in entries:
    identifier = entry.get("id") if isinstance(entry, dict) else None
    if not isinstance(identifier, str) or not identifier:
        fail("every bibliography entry must have a non-empty id")
    if identifier in available:
        fail(f"duplicate bibliography key: {identifier}")
    available.add(identifier)

ast = json.loads(run("pandoc", *chapters, "--from=markdown", "--to=json"))
cited = citation_ids(ast)
if not cited:
    fail("starter fixture must contain at least one citation")
missing = sorted(cited - available)
if missing:
    fail(f"missing citation keys: {', '.join(missing)}")

print(
    f"project assertions: {len(chapters)} sources, "
    f"{len(cited)} cited keys, {len(available)} bibliography entries"
)
