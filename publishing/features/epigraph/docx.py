#!/usr/bin/env python3
"""Add the DOCX paragraph styles emitted by the optional epigraph filter."""

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
    replace_property,
    xml,
    xml_bytes,
)


WIDTHS = (("60", "1587"), ("75", "992"), ("Full", "0"))


def configure_paragraph(
    style,
    *,
    indent: str,
    alignment: str,
    before: str,
    after: str,
    keep_next: bool,
    separator: bool = False,
) -> None:
    properties = ensure_child(style, W("pPr"))
    replace_property(properties, W("spacing"), {"before": before, "after": after})
    replace_property(
        properties,
        W("ind"),
        {"left": indent, "right": indent, "firstLine": "0"},
    )
    replace_property(properties, W("jc"), {"val": alignment})
    for child in list(properties):
        if child.tag == W("keepNext"):
            properties.remove(child)
    if keep_next:
        replace_property(properties, W("keepNext"))
    for child in list(properties):
        if child.tag == W("pBdr"):
            properties.remove(child)
    if separator:
        borders = replace_property(properties, W("pBdr"))
        replace_property(
            borders,
            W("bottom"),
            {"val": "single", "sz": "4", "space": "6", "color": "auto"},
        )


def configure_styles(data: bytes) -> bytes:
    root = xml(data, "word/styles.xml")
    for suffix, indent in WIDTHS:
        for front in (False, True):
            prefix = "FrontEpigraph" if front else "Epigraph"
            display = "Front Epigraph" if front else "Epigraph"
            text_id = f"{prefix}Text{suffix}"
            source_id = f"{prefix}Source{suffix}"
            text = ensure_style(
                root,
                text_id,
                f"{display} Text {suffix}",
                next_style=source_id,
            )
            configure_paragraph(
                text,
                indent=indent,
                alignment="left",
                before="1440" if front else "0",
                after="0",
                keep_next=True,
            )
            source = ensure_style(
                root,
                source_id,
                f"{display} Source {suffix}",
                next_style="Normal",
            )
            configure_paragraph(
                source,
                indent=indent,
                alignment="right",
                before="193",
                after="193",
                keep_next=False,
            )
            if not front:
                separator_id = f"{source_id}Separator"
                separator = ensure_style(
                    root,
                    separator_id,
                    f"{display} Source {suffix} Separator",
                    next_style="Normal",
                )
                configure_paragraph(
                    separator,
                    indent=indent,
                    alignment="right",
                    before="193",
                    after="193",
                    keep_next=False,
                    separator=True,
                )
    first = ensure_style(
        root, "FirstParagraph", "First Paragraph", next_style="Normal"
    )
    properties = ensure_child(first, W("pPr"))
    replace_property(properties, W("ind"), {"firstLine": "0"})
    return xml_bytes(root)


def process(path: Path) -> None:
    package = DocxPackage(path)
    package.parts["word/styles.xml"] = configure_styles(
        package.parts["word/styles.xml"]
    )
    package.write()


def main() -> None:
    for path in listed_docx_files(sys.argv[1:]):
        process(path)


if __name__ == "__main__":
    main()
