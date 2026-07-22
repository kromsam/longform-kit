#!/usr/bin/env python3
"""Internal OOXML helpers for Longform Kit's optional DOCX features."""

from __future__ import annotations

from collections import OrderedDict
import os
from pathlib import Path
import tempfile
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZIP_DEFLATED, ZipFile, ZipInfo


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
ET.register_namespace("w", W_NS)
ET.register_namespace("r", R_NS)


def qn(namespace: str, name: str) -> str:
    return f"{{{namespace}}}{name}"


def W(name: str) -> str:
    return qn(W_NS, name)


def xml(data: bytes, label: str = "OOXML part") -> ET.Element:
    try:
        return ET.fromstring(data)
    except ET.ParseError as error:
        raise RuntimeError(f"{label} is not valid XML: {error}") from error


def xml_bytes(root: ET.Element) -> bytes:
    return ET.tostring(
        root, encoding="UTF-8", xml_declaration=True, short_empty_elements=True
    )


def paragraph_style(paragraph: ET.Element) -> str | None:
    style = paragraph.find(f"./{W('pPr')}/{W('pStyle')}")
    return None if style is None else style.get(W("val"))


def find_style(styles: ET.Element, style_id: str) -> ET.Element | None:
    return next(
        (
            item
            for item in styles.findall(W("style"))
            if item.get(W("styleId")) == style_id
        ),
        None,
    )


def replace_property(
    parent: ET.Element, tag: str, attributes: dict[str, str] | None = None
) -> ET.Element:
    matches = [child for child in list(parent) if child.tag == tag]
    if matches:
        child = matches[0]
        for duplicate in matches[1:]:
            parent.remove(duplicate)
        child.attrib.clear()
    else:
        child = ET.SubElement(parent, tag)
    for name, value in (attributes or {}).items():
        child.set(W(name), value)
    return child


def ensure_style(
    styles: ET.Element,
    style_id: str,
    name: str,
    *,
    based_on: str = "Normal",
    next_style: str = "Normal",
) -> ET.Element:
    style = find_style(styles, style_id)
    if style is None:
        style = ET.SubElement(
            styles,
            W("style"),
            {
                W("type"): "paragraph",
                W("styleId"): style_id,
                W("customStyle"): "1",
            },
        )
    replace_property(style, W("name"), {"val": name})
    replace_property(style, W("basedOn"), {"val": based_on})
    replace_property(style, W("next"), {"val": next_style})
    return style


def ensure_child(parent: ET.Element, tag: str) -> ET.Element:
    child = parent.find(tag)
    if child is None:
        child = ET.SubElement(parent, tag)
    return child


def listed_docx_files(arguments: list[str] | None = None) -> list[Path]:
    if arguments:
        candidates = arguments
    else:
        candidates = os.environ.get("QUARTO_PROJECT_OUTPUT_FILES", "").splitlines()
    return [
        (Path.cwd() / item.strip()).resolve()
        for item in candidates
        if item.strip().lower().endswith(".docx")
    ]


class DocxPackage:
    """Read and atomically rewrite a DOCX package without losing ZIP metadata."""

    def __init__(self, path: Path):
        self.path = path
        self.infos: OrderedDict[str, ZipInfo] = OrderedDict()
        self.parts: dict[str, bytes] = {}
        try:
            with ZipFile(path) as archive:
                corrupt = archive.testzip()
                if corrupt:
                    raise RuntimeError(
                        f"DOCX package {path} contains a corrupt member: {corrupt}"
                    )
                for info in archive.infolist():
                    self.infos[info.filename] = info
                    self.parts[info.filename] = archive.read(info.filename)
        except (BadZipFile, OSError) as error:
            raise RuntimeError(f"cannot read DOCX package {path}: {error}") from error
        for required in ("word/document.xml", "word/styles.xml"):
            if required not in self.parts:
                raise RuntimeError(f"DOCX package {path} is missing {required}")

    def write(self, output: Path | None = None) -> None:
        destination = output or self.path
        destination.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.stem}-", suffix=".docx", dir=destination.parent
        )
        os.close(descriptor)
        temporary = Path(temporary_name)
        try:
            with ZipFile(temporary, "w") as archive:
                for name, info in self.infos.items():
                    if name not in self.parts:
                        continue
                    clone = ZipInfo(name, info.date_time)
                    for attribute in (
                        "compress_type",
                        "comment",
                        "extra",
                        "create_system",
                        "create_version",
                        "extract_version",
                        "external_attr",
                        "internal_attr",
                        "flag_bits",
                    ):
                        setattr(clone, attribute, getattr(info, attribute))
                    archive.writestr(clone, self.parts[name])
                for name in sorted(set(self.parts) - set(self.infos)):
                    info = ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                    info.compress_type = ZIP_DEFLATED
                    info.external_attr = 0o600 << 16
                    archive.writestr(info, self.parts[name])
            if destination.exists() and destination.read_bytes() == temporary.read_bytes():
                temporary.unlink()
            else:
                temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
