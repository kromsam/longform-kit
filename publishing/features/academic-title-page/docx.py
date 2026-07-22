#!/usr/bin/env python3
"""Supply academic-title styles and deterministic field order in DOCX output."""

from __future__ import annotations

from pathlib import Path
import sys

sys.dont_write_bytecode = True
SHARED = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED))

from ooxml import (  # noqa: E402
    DocxPackage,
    W,
    ensure_child,
    ensure_style,
    listed_docx_files,
    paragraph_style,
    replace_property,
    xml,
    xml_bytes,
)


FIELD_ORDER = (
    "Title",
    "Subtitle",
    "Author",
    "StudentNumber",
    "Degree",
    "Supervisor",
    "Date",
    "Institute",
)


def configure_styles(data: bytes) -> bytes:
    root = xml(data, "word/styles.xml")
    specifications = (
        ("StudentNumber", "Student Number", "Degree"),
        ("Degree", "Degree", "Supervisor"),
        ("Supervisor", "Supervisor", "Date"),
        ("Institute", "Institute", "Normal"),
    )
    for style_id, name, next_style in specifications:
        style = ensure_style(root, style_id, name, next_style=next_style)
        paragraph = ensure_child(style, W("pPr"))
        replace_property(paragraph, W("jc"), {"val": "center"})
        replace_property(paragraph, W("keepNext"))
    return xml_bytes(root)


def reorder_fields(data: bytes) -> bytes:
    root = xml(data, "word/document.xml")
    body = root.find(W("body"))
    if body is None:
        raise RuntimeError("DOCX document.xml has no body")
    found: dict[str, list] = {style: [] for style in FIELD_ORDER}
    for paragraph in body.findall(W("p")):
        style = paragraph_style(paragraph)
        if style in found:
            found[style].append(paragraph)
    duplicates = [style for style, items in found.items() if len(items) > 1]
    if duplicates:
        raise RuntimeError(
            "academic title fields must occur at most once: " + ", ".join(duplicates)
        )
    ordered = [found[style][0] for style in FIELD_ORDER if found[style]]
    if not ordered:
        raise RuntimeError("academic title page requires standard title metadata")
    first_index = min(list(body).index(item) for item in ordered)
    for item in ordered:
        body.remove(item)
    for offset, item in enumerate(ordered):
        body.insert(first_index + offset, item)
    return xml_bytes(root)


def process(path: Path) -> None:
    package = DocxPackage(path)
    package.parts["word/styles.xml"] = configure_styles(
        package.parts["word/styles.xml"]
    )
    package.parts["word/document.xml"] = reorder_fields(
        package.parts["word/document.xml"]
    )
    package.write()


def main() -> None:
    for path in listed_docx_files(sys.argv[1:]):
        process(path)


if __name__ == "__main__":
    main()
