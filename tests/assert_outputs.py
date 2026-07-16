#!/usr/bin/env python3
"""Structural assertions for Longform Kit's normalized build artefacts."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from zipfile import ZipFile
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = ROOT / "document"
QUARTO = os.environ.get("QUARTO") or os.environ.get("LONGFORM_QUARTO") or "quarto"
WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def fail(message: str) -> None:
    raise AssertionError(message)


def require_file(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        fail(f"missing or empty output: {path.relative_to(ROOT)}")


def assert_order(text: str, values: list[str], label: str) -> None:
    position = -1
    for value in values:
        found = text.find(value, position + 1)
        if found < 0:
            fail(f"{label} is missing ordered content: {value!r}")
        position = found


def inspect() -> dict:
    output = subprocess.run(
        [QUARTO, "inspect"],
        cwd=DOCUMENT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout
    return json.loads(output)["config"]


def assert_gfm(path: Path, title: str) -> None:
    require_file(path)
    text = path.read_text(encoding="utf-8")
    if text.startswith("---\n"):
        fail("default Markdown-derived GFM unexpectedly uses the LaTeX-mode YAML header")
    assert_order(
        text,
        [
            f"# {title}",
            "Every long document begins with a first page.",
            "# Introduction",
            "# Conclusion",
            "# Bibliography",
        ],
        "GFM",
    )
    for expected in ("[^1]", "The Example Book", "2nd ed.", "Example Press", "1–2"):
        if expected not in text:
            fail(f"GFM is missing citation content: {expected!r}")
    note = re.search(r"^\[\^1\]:(.*(?:\n(?: {4}|\t).*)*)", text, re.MULTILINE)
    if note is None:
        fail("GFM does not contain the expected citation footnote definition")
    normalized_note = re.sub(r"\s+", " ", note.group(0))
    for expected in (
        "Alex Example",
        "The Example Book",
        "2nd ed.",
        "Example Press",
        "1–2",
    ):
        if expected not in normalized_note:
            fail(f"GFM citation footnote is missing content: {expected!r}")
    if "`../bin/longform build all`" not in text:
        fail("Markdown-derived GFM changed spaces inside the sample code span")
    for leaked in ("\\chapter", "\\epigraph", "\\newpage", "::: {.epigraph"):
        if leaked in text:
            fail(f"GFM contains output-specific source markup: {leaked!r}")


def assert_latex(path: Path) -> None:
    require_file(path)
    text = path.read_text(encoding="utf-8")
    for expected in (
        "\\documentclass[",
        "\\usepackage[twoside,left=36mm,right=36mm]{geometry}",
        "  hidelinks,",
        "\\tableofcontents",
        "\\begin{CSLReferences}",
        "The Example Book",
        "2nd ed.",
    ):
        if expected not in text:
            fail(f"LaTeX is missing structural content: {expected!r}")
    if "$if(" in text or "$endif$" in text:
        fail("LaTeX contains unexpanded Pandoc template directives")
    assert_order(
        text,
        [
            "\\maketitle",
            "Every long document begins with a first page.",
            "\\tableofcontents",
            "\\chapter*{Introduction}",
            "\\chapter*{Conclusion}",
            "\\chapter*{Bibliography}",
        ],
        "LaTeX",
    )


def qn(name: str) -> str:
    return f"{{{WORD_NS}}}{name}"


def xml_text(root: ET.Element) -> str:
    return " ".join(node.text or "" for node in root.iter(qn("t")))


def attribute_values(root: ET.Element, element: str, attribute: str) -> set[str]:
    return {
        value
        for node in root.iter(qn(element))
        if (value := node.get(qn(attribute))) is not None
    }


def assert_docx(path: Path, title: str) -> None:
    require_file(path)
    required = {
        "[Content_Types].xml",
        "word/document.xml",
        "word/styles.xml",
        "word/settings.xml",
        "word/footnotes.xml",
    }
    with ZipFile(path) as archive:
        corrupt = archive.testzip()
        if corrupt:
            fail(f"DOCX contains a corrupt member: {corrupt}")
        missing = required - set(archive.namelist())
        if missing:
            fail(f"DOCX is missing package members: {', '.join(sorted(missing))}")
        document = ET.fromstring(archive.read("word/document.xml"))
        styles = ET.fromstring(archive.read("word/styles.xml"))
        settings = ET.fromstring(archive.read("word/settings.xml"))
        footnotes = ET.fromstring(archive.read("word/footnotes.xml"))

    assert_order(
        xml_text(document),
        [
            title,
            "Every long document begins with a first page.",
            "Contents",
            "Introduction",
            "Conclusion",
            "Bibliography",
        ],
        "DOCX",
    )

    style_ids = attribute_values(styles, "style", "styleId")
    expected_styles = {"TOCHeading", "EpigraphText", "EpigraphSource", "Bibliography"}
    missing_styles = expected_styles - style_ids
    if missing_styles:
        fail(f"DOCX reference styles are missing: {', '.join(sorted(missing_styles))}")

    paragraph_styles = attribute_values(document, "pStyle", "val")
    missing_usage = expected_styles - paragraph_styles
    if missing_usage:
        fail(f"DOCX does not apply styles: {', '.join(sorted(missing_usage))}")

    instructions = " ".join(node.text or "" for node in document.iter(qn("instrText")))
    if 'TOC \\o "1-2" \\h \\z \\u' not in instructions:
        fail("DOCX does not contain the expected level 1-2 TOC field")
    if "true" not in attribute_values(document, "fldChar", "dirty"):
        fail("DOCX TOC field is not marked dirty for refresh")

    page_breaks = sum(
        node.get(qn("type")) == "page" for node in document.iter(qn("br"))
    )
    if page_breaks < 3:
        fail(f"DOCX has too few explicit page breaks: {page_breaks}")
    if "true" not in attribute_values(settings, "updateFields", "val"):
        fail("DOCX does not request field updates when opened")
    if "The Example Book" not in xml_text(footnotes):
        fail("DOCX footnotes do not contain the rendered citation")
    if "2nd ed." not in xml_text(footnotes):
        fail("DOCX footnotes do not preserve the abbreviated edition label")


def command_output(*args: str) -> str:
    return subprocess.run(
        args,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    ).stdout


def assert_pdf_file(path: Path, title: str) -> tuple[int, str]:
    require_file(path)
    if shutil.which("qpdf"):
        command_output("qpdf", "--check", str(path))

    info = command_output("pdfinfo", str(path))
    pages_match = re.search(r"^Pages:\s+(\d+)$", info, re.MULTILINE)
    if not pages_match or int(pages_match.group(1)) < 1:
        fail(f"PDF has no pages: {path.name}")
    page_size = re.search(r"^Page size:\s+(.+)$", info, re.MULTILINE)
    if not page_size or "A4" not in page_size.group(1):
        fail(f"PDF is not A4: {path.name}")

    fonts = command_output("pdffonts", str(path)).splitlines()[2:]
    font_rows = [line for line in fonts if line.strip()]
    if not font_rows:
        fail(f"PDF contains no inspectable fonts: {path.name}")
    for row in font_rows:
        flags = re.search(r"\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$", row)
        if not flags or flags.group(1) != "yes":
            fail(f"PDF contains a non-embedded or unparseable font row: {row}")

    text = command_output("pdftotext", "-layout", str(path), "-")
    assert_order(
        text,
        [
            title,
            "Every long document begins with a first page.",
            "Contents",
            "Introduction",
            "Conclusion",
            "Bibliography",
        ],
        path.name,
    )

    physical_pages = text.split("\f")
    for heading in ("Introduction", "Conclusion", "Bibliography"):
        matches = [
            index + 1
            for index, page in enumerate(physical_pages)
            if re.search(rf"^\s*{re.escape(heading)}\s*$", page, re.MULTILINE)
        ]
        if not matches:
            fail(f"could not locate {heading!r} chapter page in {path.name}")
        if matches[-1] % 2 == 0:
            fail(f"{heading!r} does not begin on a recto page in {path.name}")

    return int(pages_match.group(1)), text


def assert_pdfs(path: Path, binding: Path, title: str) -> None:
    pages, text = assert_pdf_file(path, title)
    binding_pages, binding_text = assert_pdf_file(binding, title)
    if pages != binding_pages:
        fail("equal-margin and binding PDFs have different page counts")
    normalized_text = re.sub(r"\s+", " ", text).strip()
    normalized_binding_text = re.sub(r"\s+", " ", binding_text).strip()
    if normalized_text != normalized_binding_text:
        fail("equal-margin and binding PDFs contain different extracted text")
    if path.read_bytes() == binding.read_bytes():
        fail("equal-margin and binding PDFs are byte-identical; profile was not applied")


if len(sys.argv) != 2 or sys.argv[1] not in {"gfm", "docx", "latex", "pdf"}:
    print("usage: assert_outputs.py gfm|docx|latex|pdf", file=sys.stderr)
    raise SystemExit(2)

target = sys.argv[1]
config = inspect()
output_dir = DOCUMENT / config.get("project", {}).get("output-dir", "build")
base = config.get("book", {}).get("output-file", "longform-document")
title = config.get("book", {}).get("title", "Longform document")

if target == "gfm":
    assert_gfm(output_dir / f"{base}.md", title)
elif target == "docx":
    assert_docx(output_dir / f"{base}.docx", title)
elif target == "latex":
    assert_latex(output_dir / f"{base}.tex")
else:
    assert_pdfs(
        output_dir / f"{base}.pdf",
        output_dir / f"{base}-binding.pdf",
        title,
    )

print(f"output assertions: {target} passed")
