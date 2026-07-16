#!/usr/bin/env python3
"""Focused regression tests for reusable Longform Kit filter behavior."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any
from zipfile import ZipFile
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = ROOT / "document"
EXTENSION = DOCUMENT / "_extensions/longform-kit"
QUARTO = os.environ.get("QUARTO") or os.environ.get("LONGFORM_QUARTO") or "quarto"
WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def fail(message: str) -> None:
    raise AssertionError(message)


def qn(name: str) -> str:
    return f"{{{WORD_NS}}}{name}"


def paragraph_text(paragraph: ET.Element) -> str:
    return "".join(node.text or "" for node in paragraph.iter(qn("t")))


def paragraph_style(paragraph: ET.Element) -> str | None:
    style = paragraph.find(f"./{qn('pPr')}/{qn('pStyle')}")
    return style.get(qn("val")) if style is not None else None


def page_breaks(paragraph: ET.Element) -> list[ET.Element]:
    return [
        node for node in paragraph.iter(qn("br"))
        if node.get(qn("type")) == "page"
    ]


def style_by_id(styles: ET.Element, style_id: str) -> ET.Element:
    style = next(
        (
            node for node in styles.iter(qn("style"))
            if node.get(qn("styleId")) == style_id
        ),
        None,
    )
    if style is None:
        fail(f"DOCX reference document is missing style {style_id}")
    return style


def assert_docx_options() -> None:
    with tempfile.TemporaryDirectory(prefix="longform-extension-") as directory:
        output = Path(directory) / "options.docx"
        subprocess.run(
            [
                QUARTO,
                "pandoc",
                str(ROOT / "tests/fixtures/docx-options.md"),
                "--from=markdown",
                "--to=docx",
                "--standalone",
                f"--reference-doc={EXTENSION / 'reference.docx'}",
                f"--lua-filter={EXTENSION / 'pagebreak.lua'}",
                f"--lua-filter={EXTENSION / 'longform.lua'}",
                f"--output={output}",
            ],
            cwd=DOCUMENT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        with ZipFile(output) as archive:
            corrupt = archive.testzip()
            if corrupt:
                fail(f"focused DOCX fixture contains a corrupt member: {corrupt}")
            document = ET.fromstring(archive.read("word/document.xml"))
            styles = ET.fromstring(archive.read("word/styles.xml"))
            settings = ET.fromstring(archive.read("word/settings.xml"))

    instructions = " ".join(
        node.text or "" for node in document.iter(qn("instrText"))
    ).strip()
    if instructions != 'TOC \\o "1-1" \\h':
        fail(f"DOCX TOC depth or switches changed: {instructions!r}")

    if not any(
        node.get(qn("dirty")) == "true" for node in document.iter(qn("fldChar"))
    ):
        fail("DOCX TOC field is not marked dirty")
    if not any(
        node.get(qn("val")) == "true" for node in settings.iter(qn("updateFields"))
    ):
        fail("DOCX does not request field updates on open")

    body = document.find(qn("body"))
    if body is None:
        fail("DOCX fixture has no document body")
    body_children = list(body)
    toc_index = next(
        (index for index, child in enumerate(body_children) if child.tag == qn("sdt")),
        None,
    )
    if toc_index is None or toc_index == 0:
        fail("DOCX fixture has no TOC container or leading paragraph")
    toc_blank = body_children[toc_index - 1]
    if (
        toc_blank.tag != qn("p")
        or paragraph_text(toc_blank)
        or paragraph_style(toc_blank) != "Normal"
    ):
        fail("DOCX TOC opt-in leading blank is not an empty Normal paragraph")

    toc_heading = next(
        (
            paragraph for paragraph in document.iter(qn("p"))
            if paragraph_style(paragraph) == "TOCHeading"
        ),
        None,
    )
    if toc_heading is None or not page_breaks(toc_heading):
        fail("DOCX TOC heading opt-in page break is missing")

    heading2 = style_by_id(styles, "Heading2")
    heading2_break = heading2.find(f"./{qn('pPr')}/{qn('pageBreakBefore')}")
    if heading2_break is None or heading2_break.get(qn("val")) != "false":
        fail("Heading2 must explicitly disable page-break-before")

    flush = style_by_id(styles, "EpigraphTextFlush")
    based_on = flush.find(f"./{qn('basedOn')}")
    indent = flush.find(f"./{qn('pPr')}/{qn('ind')}")
    if based_on is None or based_on.get(qn("val")) != "EpigraphText":
        fail("Epigraph Text Flush must inherit from Epigraph Text")
    if indent is None or any(
        indent.get(qn(attribute)) != "0" for attribute in ("left", "hanging")
    ):
        fail("Epigraph Text Flush must reset left and hanging indents")

    paragraphs = list(document.iter(qn("p")))
    by_text = {paragraph_text(paragraph): paragraph for paragraph in paragraphs}
    front = by_text.get("Front fixture quotation.")
    chapter = by_text.get("Chapter fixture quotation.")
    if front is None or paragraph_style(front) != "EpigraphText":
        fail("front epigraph does not use Epigraph Text")
    if next(front.iter(qn("br")), None) is not None:
        fail("front epigraph unexpectedly received the chapter leading break")
    if chapter is None or paragraph_style(chapter) != "EpigraphTextFlush":
        fail("docx-flush chapter epigraph does not use Epigraph Text Flush")
    chapter_content = [
        node.tag for node in chapter.iter()
        if node.tag in {qn("br"), qn("t")}
    ]
    if not chapter_content or chapter_content[0] != qn("br"):
        fail("chapter epigraph opt-in leading break is missing")

    chapter_source_index = next(
        (
            index for index, paragraph in enumerate(paragraphs)
            if paragraph_style(paragraph) == "EpigraphSource"
            and "Chapter fixture source" in paragraph_text(paragraph)
        ),
        None,
    )
    if chapter_source_index is None:
        fail("chapter epigraph source is missing")
    following = paragraphs[chapter_source_index + 1 : chapter_source_index + 3]
    if len(following) != 2:
        fail("chapter epigraph is missing its separator or following paragraph")
    separator, first_paragraph = following
    if paragraph_text(separator) or not any(
        node.tag == qn("pict") for node in separator.iter()
    ):
        fail("chapter epigraph separator is not emitted as a DOCX horizontal rule")
    if (
        paragraph_text(first_paragraph)
        != "First paragraph after the chapter epigraph."
        or paragraph_style(first_paragraph) != "FirstParagraph"
    ):
        fail("prose after a chapter epigraph must use First Paragraph")

    bibliography_index = next(
        (
            index for index, paragraph in enumerate(paragraphs)
            if paragraph_text(paragraph) == "Bibliography"
        ),
        None,
    )
    if bibliography_index is None or bibliography_index == 0:
        fail("DOCX fixture bibliography heading is missing")
    if not page_breaks(paragraphs[bibliography_index - 1]):
        fail("configured bibliography page break is missing")
    if bibliography_index + 2 >= len(paragraphs):
        fail("DOCX fixture bibliography body is missing")
    bibliography_blank = paragraphs[bibliography_index + 1]
    bibliography_entry = paragraphs[bibliography_index + 2]
    if (
        paragraph_text(bibliography_blank)
        or paragraph_style(bibliography_blank) != "FirstParagraph"
    ):
        fail("bibliography leading blank is not an empty First Paragraph")
    if paragraph_style(bibliography_entry) != "Bibliography":
        fail("bibliography entry does not use the Bibliography style")


def walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def render_note_ast(enabled: bool | None) -> dict[str, Any]:
    option = ""
    if enabled is not None:
        option = (
            "longform:\n"
            f"  preserve-attached-note-positions: {'true' if enabled else 'false'}\n"
        )
    source = "\n".join(
        [
            "---",
            "bibliography: references/library.json",
            "csl: references/style.csl",
            option.rstrip("\n"),
            "---",
            "Attached[@exampleBook2024, 1]. Spaced [@exampleBook2024, 2].",
            "",
        ]
    )
    result = subprocess.run(
        [
            QUARTO,
            "pandoc",
            "--from=markdown",
            "--to=json",
            f"--lua-filter={EXTENSION / 'longform.lua'}",
        ],
        cwd=DOCUMENT,
        check=True,
        input=source,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return json.loads(result.stdout)


def find_body_para(ast: dict[str, Any]) -> dict[str, Any]:
    paragraph = next(
        (
            block for block in ast.get("blocks", [])
            if block.get("t") == "Para"
            and any(
                node.get("t") == "Str" and node.get("c") == "Attached"
                for node in block.get("c", [])
            )
        ),
        None,
    )
    if paragraph is None:
        fail("attached-note fixture paragraph is missing from the Pandoc AST")
    return paragraph


def assert_attached_notes() -> None:
    default = find_body_para(render_note_ast(None))
    explicit_false = find_body_para(render_note_ast(False))
    enabled = find_body_para(render_note_ast(True))

    def note_spans(paragraph: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            node for node in walk(paragraph)
            if node.get("t") == "Span"
            and "note-before-punctuation" in node.get("c", [[], []])[0][1]
        ]

    if note_spans(default) or note_spans(explicit_false):
        fail("attached-note compatibility behavior must remain opt-in")
    spans = note_spans(enabled)
    if len(spans) != 1:
        fail(f"attached-note opt-in wrapped {len(spans)} citations instead of one")

    enabled_inlines = enabled["c"]
    attached_span_index = enabled_inlines.index(spans[0])
    if (
        attached_span_index + 1 >= len(enabled_inlines)
        or enabled_inlines[attached_span_index + 1].get("t") != "Str"
        or enabled_inlines[attached_span_index + 1].get("c") != "."
    ):
        fail("attached-note opt-in did not leave punctuation after the wrapped note")

    if sum(node.get("t") == "Note" for node in walk(enabled)) != 2:
        fail("attached-note opt-in changed the number of rendered citation notes")
    if sum(node.get("t") == "Span" for node in walk(enabled)) != 1:
        fail("attached-note opt-in also wrapped the ordinary spaced citation")


assert_docx_options()
assert_attached_notes()
print("extension assertions: DOCX options and attached-note placement passed")
