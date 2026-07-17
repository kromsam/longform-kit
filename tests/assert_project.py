#!/usr/bin/env python3
"""Assert the native Quarto project, author boundary, and citations agree."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = ROOT / "document"
QUARTO_DIRECTORY = ROOT / "quarto"
PROJECT_CONFIG = QUARTO_DIRECTORY / "project.yml"
BINDING_CONFIG = QUARTO_DIRECTORY / "binding.yml"
QUARTO = os.environ.get("QUARTO") or os.environ.get("LONGFORM_QUARTO") or "quarto"


def fail(message: str) -> None:
    raise AssertionError(message)


def run(*args: str) -> str:
    result = subprocess.run(
        [QUARTO, *args],
        cwd=ROOT,
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
information = inspection.get("fileInformation", {})

root_loader = ROOT / "_quarto.yml"
root_index = ROOT / "index.md"
for path in (root_loader, root_index, PROJECT_CONFIG, BINDING_CONFIG):
    if not path.is_file():
        fail(f"required Quarto file is missing: {path.relative_to(ROOT)}")
    if path.is_symlink():
        fail(f"Quarto file must not be a symlink: {path.relative_to(ROOT)}")
if (ROOT / "_quarto-binding.yml").exists():
    fail("binding configuration must live in quarto/binding.yml")
if (ROOT / "_extensions").exists():
    fail("vendored extensions must live under quarto/extensions/")

expected_config_files = [
    root_loader.resolve(),
    PROJECT_CONFIG.resolve(),
    (DOCUMENT / "metadata.yml").resolve(),
    (DOCUMENT / "chapters.yml").resolve(),
]
resolved_config_files = [
    Path(path).resolve() for path in inspection.get("files", {}).get("config", [])
]
if resolved_config_files != expected_config_files:
    fail("root _quarto.yml must load the configuration files in canonical order")

if project.get("type") != "book":
    fail("project.type must use Quarto's native book type")
if project.get("output-dir") != "build":
    fail("generated output must live at the repository root in build/")
if set(config.get("format", {})) != {"pdf", "docx", "latex"}:
    fail("the project must declare only native pdf, docx, and latex formats")
for name, options in config["format"].items():
    if isinstance(options, dict) and options.get("citeproc") is False:
        fail(f"{name} disables Quarto's native citeproc processing")
if config["format"]["docx"].get("toc") is not True:
    fail("DOCX must use Quarto's native table of contents")
reference_doc = config["format"]["docx"].get("reference-doc")
if not isinstance(reference_doc, str) or not (ROOT / reference_doc).is_file():
    fail("DOCX must use a project-local reference document")

if not chapters or not all(isinstance(path, str) for path in chapters):
    fail("Quarto did not resolve an ordered list of source files")
include_map = information.get("index.md", {}).get("includeMap", [])
if include_map != [
    {
        "source": str((ROOT / "index.md").resolve()),
        "target": "document/front-matter.md",
    }
]:
    fail("index.md must be a one-line adapter for document/front-matter.md")

author_files = ["document/front-matter.md", *chapters[1:]]
for relative in author_files:
    path = (ROOT / relative).resolve()
    try:
        path.relative_to(DOCUMENT.resolve())
    except ValueError:
        fail(f"author source escapes document/: {relative}")
    if path.suffix != ".md" or not path.is_file():
        fail(f"author source is not Markdown: {relative}")

metadata_file = DOCUMENT / "metadata.yml"
chapters_file = DOCUMENT / "chapters.yml"
zettlr_adapter = DOCUMENT / ".ztr-directory"
# metadata.yml and chapters.yml are author-owned; .ztr-directory is the
# generated Zettlr adapter. All three are the permitted non-Markdown files.
author_metadata = {metadata_file, chapters_file, zettlr_adapter}
if not metadata_file.is_file():
    fail("manuscript metadata must live in document/metadata.yml")
if not chapters_file.is_file():
    fail("the chapter list must live in document/chapters.yml")
if not book.get("title"):
    fail("book.title must resolve through document/metadata.yml")
if not config.get("lang"):
    fail("lang must resolve through document/metadata.yml")
if not book.get("chapters"):
    fail("book.chapters must resolve through document/chapters.yml")

unexpected = [
    path.relative_to(DOCUMENT)
    for path in DOCUMENT.rglob("*")
    if path.is_file() and path.suffix != ".md" and path not in author_metadata
]
if unexpected:
    fail(f"document/ contains non-author files: {', '.join(map(str, unexpected))}")

extension = QUARTO_DIRECTORY / "extensions" / "epigraph"
manifest = (extension / "_extension.yml").read_text(encoding="utf-8")
if "version: 0.0.1" not in manifest:
    fail("Fancy Epigraphs must remain pinned at v0.0.1")
if (QUARTO_DIRECTORY / "extensions" / "longform-kit").exists():
    fail("the retired custom Longform Kit extension is still present")
if config.get("shortcodes") != ["quarto/extensions/epigraph/epigraph.lua"]:
    fail("quarto/project.yml must register the relocated epigraph shortcode")
if "{{< epigraph " not in (DOCUMENT / "front-matter.md").read_text(encoding="utf-8"):
    fail("starter front matter does not exercise Fancy Epigraphs")
if "{{< pagebreak >}}" not in (DOCUMENT / "front-matter.md").read_text(encoding="utf-8"):
    fail("starter front matter does not use Quarto's native pagebreak shortcode")

csl = config.get("csl")
if not isinstance(csl, str) or not csl:
    fail("quarto/project.yml must declare one configured CSL file")
csl_path = ROOT / csl
if not csl_path.is_symlink() or not csl_path.is_file():
    fail(f"CSL file does not exist: {csl}")
styles_path = ROOT / "references" / "zotero-styles"
if not styles_path.is_symlink() or not styles_path.is_dir():
    fail("Zotero styles directory is not linked by setup")
expected_resource_path = [
    ".",
    "references/.csl-parents",
    "references/zotero-styles",
    "references/zotero-styles/hidden",
]
if config.get("resource-path") != expected_resource_path:
    fail("quarto/project.yml does not retain the citation resource path")

# The adapter lives in document/, so its paths are relative to that directory.
def document_relative(path):
    if path.startswith("document/"):
        return path[len("document/"):]
    return f"../{path}"


expected_zettlr = {
    "sorting": "name-up",
    "project": {
        "title": book.get("title", "Longform document"),
        "profiles": [],
        "files": [document_relative(path) for path in author_files],
        "cslStyle": document_relative(csl),
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
    fail("Longform Kit requires exactly one bibliography")

bibliography_path = ROOT / bibliographies[0]
if not bibliography_path.is_symlink():
    fail("bibliography is not linked by setup")
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

ast = json.loads(run("pandoc", *author_files, "--from=markdown", "--to=json"))
cited = citation_ids(ast)
if not cited:
    fail("starter fixture must contain at least one citation")
missing = sorted(cited - available)
if missing:
    fail(f"missing citation keys: {', '.join(missing)}")

print(
    f"project assertions: {len(author_files)} author sources, "
    f"{len(cited)} cited keys, {len(available)} bibliography entries"
)
