#!/usr/bin/env python3
"""Deterministic OOXML policy for the optional Longform DOCX design.

The module deliberately uses only Python's standard library. It is shared by
the reference-document generator and the pre-/post-LibreOffice hooks, keeping
the typography policy in one place and making every transform idempotent.
"""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import struct
import sys
import uuid
from xml.etree import ElementTree as ET

SHARED = Path(__file__).resolve().parents[1] / "_shared"
if str(SHARED) not in sys.path:
    sys.path.insert(0, str(SHARED))

from ooxml import DocxPackage, listed_docx_files  # noqa: E402


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W14_NS = "http://schemas.microsoft.com/office/word/2010/wordml"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
CP_NS = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC_NS = "http://purl.org/dc/elements/1.1/"
DCTERMS_NS = "http://purl.org/dc/terms/"
DCMITYPE_NS = "http://purl.org/dc/dcmitype/"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
XML_NS = "http://www.w3.org/XML/1998/namespace"
CUSTOM_PROPERTIES_NS = (
    "http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"
)
VT_NS = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"

ET.register_namespace("w", W_NS)
ET.register_namespace("w14", W14_NS)
ET.register_namespace("r", R_NS)
ET.register_namespace("", REL_NS)
ET.register_namespace("cp", CP_NS)
ET.register_namespace("dc", DC_NS)
ET.register_namespace("dcterms", DCTERMS_NS)
ET.register_namespace("dcmitype", DCMITYPE_NS)
ET.register_namespace("xsi", XSI_NS)
ET.register_namespace("custom", CUSTOM_PROPERTIES_NS)
ET.register_namespace("vt", VT_NS)


def qn(namespace: str, name: str) -> str:
    return f"{{{namespace}}}{name}"


W = lambda name: qn(W_NS, name)
W14 = lambda name: qn(W14_NS, name)
R = lambda name: qn(R_NS, name)
REL = lambda name: qn(REL_NS, name)
CT = lambda name: qn(CT_NS, name)
CP = lambda name: qn(CP_NS, name)
DC = lambda name: qn(DC_NS, name)
CUSTOM = lambda name: qn(CUSTOM_PROPERTIES_NS, name)
VT = lambda name: qn(VT_NS, name)


# WordprocessingML complex types use XML Schema sequences rather than
# unordered property bags.  Word is less forgiving than LibreOffice when a
# style, paragraph, run, or section property is appended after a later
# property, so every serializer call normalizes the sequences we mutate.  The
# lists follow ISO/IEC 29500 child order; extension children retain their
# position unless explicitly listed.
CHILD_ORDER = {
    W("styles"): (
        W("docDefaults"),
        W("latentStyles"),
        W("style"),
    ),
    W("docDefaults"): (
        W("rPrDefault"),
        W("pPrDefault"),
    ),
    W("style"): (
        W("name"),
        W("aliases"),
        W("basedOn"),
        W("next"),
        W("link"),
        W("autoRedefine"),
        W("hidden"),
        W("uiPriority"),
        W("semiHidden"),
        W("unhideWhenUsed"),
        W("qFormat"),
        W("locked"),
        W("personal"),
        W("personalCompose"),
        W("personalReply"),
        W("rsid"),
        W("pPr"),
        W("rPr"),
        W("tblPr"),
        W("trPr"),
        W("tcPr"),
        W("tblStylePr"),
    ),
    W("pPr"): (
        W("pStyle"),
        W("keepNext"),
        W("keepLines"),
        W("pageBreakBefore"),
        W("framePr"),
        W("widowControl"),
        W("numPr"),
        W("suppressLineNumbers"),
        W("pBdr"),
        W("shd"),
        W("tabs"),
        W("suppressAutoHyphens"),
        W("kinsoku"),
        W("wordWrap"),
        W("overflowPunct"),
        W("topLinePunct"),
        W("autoSpaceDE"),
        W("autoSpaceDN"),
        W("bidi"),
        W("adjustRightInd"),
        W("snapToGrid"),
        W("spacing"),
        W("ind"),
        W("contextualSpacing"),
        W("mirrorIndents"),
        W("suppressOverlap"),
        W("jc"),
        W("textDirection"),
        W("textAlignment"),
        W("textboxTightWrap"),
        W("outlineLvl"),
        W("divId"),
        W("cnfStyle"),
        W("rPr"),
        W("sectPr"),
        W("pPrChange"),
    ),
    W("rPr"): (
        W("rStyle"),
        W("rFonts"),
        W("b"),
        W("bCs"),
        W("i"),
        W("iCs"),
        W("caps"),
        W("smallCaps"),
        W("strike"),
        W("dstrike"),
        W("outline"),
        W("shadow"),
        W("emboss"),
        W("imprint"),
        W("noProof"),
        W("snapToGrid"),
        W("vanish"),
        W("webHidden"),
        W("color"),
        W("spacing"),
        W("w"),
        W("kern"),
        W("position"),
        W("sz"),
        W("szCs"),
        W("highlight"),
        W("u"),
        W("effect"),
        W("bdr"),
        W("shd"),
        W("fitText"),
        W("vertAlign"),
        W("rtl"),
        W("cs"),
        W("em"),
        W("lang"),
        W("eastAsianLayout"),
        W("specVanish"),
        W("oMath"),
        W14("glow"),
        W14("shadow"),
        W14("reflection"),
        W14("textOutline"),
        W14("textFill"),
        W14("scene3d"),
        W14("props3d"),
        W14("ligatures"),
        W14("numForm"),
        W14("numSpacing"),
        W14("stylisticSets"),
        W14("cntxtAlts"),
        W("rPrChange"),
    ),
    W("sectPr"): (
        W("headerReference"),
        W("footerReference"),
        W("footnotePr"),
        W("endnotePr"),
        W("type"),
        W("pgSz"),
        W("pgMar"),
        W("paperSrc"),
        W("pgBorders"),
        W("lnNumType"),
        W("pgNumType"),
        W("cols"),
        W("formProt"),
        W("vAlign"),
        W("noEndnote"),
        W("titlePg"),
        W("textDirection"),
        W("bidi"),
        W("rtlGutter"),
        W("docGrid"),
        W("printerSettings"),
        W("sectPrChange"),
    ),
    W("settings"): (
        W("writeProtection"),
        W("view"),
        W("zoom"),
        W("removePersonalInformation"),
        W("removeDateAndTime"),
        W("doNotDisplayPageBoundaries"),
        W("displayBackgroundShape"),
        W("printPostScriptOverText"),
        W("printFractionalCharacterWidth"),
        W("printFormsData"),
        W("embedTrueTypeFonts"),
        W("embedSystemFonts"),
        W("saveSubsetFonts"),
        W("saveFormsData"),
        W("mirrorMargins"),
        W("alignBordersAndEdges"),
        W("bordersDoNotSurroundHeader"),
        W("bordersDoNotSurroundFooter"),
        W("gutterAtTop"),
        W("hideSpellingErrors"),
        W("hideGrammaticalErrors"),
        W("activeWritingStyle"),
        W("proofState"),
        W("formsDesign"),
        W("attachedTemplate"),
        W("linkStyles"),
        W("stylePaneFormatFilter"),
        W("stylePaneSortMethod"),
        W("documentType"),
        W("mailMerge"),
        W("revisionView"),
        W("trackRevisions"),
        W("doNotTrackMoves"),
        W("doNotTrackFormatting"),
        W("documentProtection"),
        W("autoFormatOverride"),
        W("styleLockTheme"),
        W("styleLockQFSet"),
        W("defaultTabStop"),
        W("autoHyphenation"),
        W("consecutiveHyphenLimit"),
        W("hyphenationZone"),
        W("doNotHyphenateCaps"),
        W("showEnvelope"),
        W("summaryLength"),
        W("clickAndTypeStyle"),
        W("defaultTableStyle"),
        W("evenAndOddHeaders"),
        W("bookFoldRevPrinting"),
        W("bookFoldPrinting"),
        W("bookFoldPrintingSheets"),
        W("drawingGridHorizontalSpacing"),
        W("drawingGridVerticalSpacing"),
        W("displayHorizontalDrawingGridEvery"),
        W("displayVerticalDrawingGridEvery"),
        W("doNotUseMarginsForDrawingGridOrigin"),
        W("drawingGridHorizontalOrigin"),
        W("drawingGridVerticalOrigin"),
        W("doNotShadeFormData"),
        W("noPunctuationKerning"),
        W("characterSpacingControl"),
        W("printTwoOnOne"),
        W("strictFirstAndLastChars"),
        W("noLineBreaksAfter"),
        W("noLineBreaksBefore"),
        W("savePreviewPicture"),
        W("doNotValidateAgainstSchema"),
        W("saveInvalidXml"),
        W("ignoreMixedContent"),
        W("alwaysShowPlaceholderText"),
        W("doNotDemarcateInvalidXml"),
        W("saveXmlDataOnly"),
        W("useXSLTWhenSaving"),
        W("saveThroughXslt"),
        W("showXMLTags"),
        W("alwaysMergeEmptyNamespace"),
        W("updateFields"),
        W("hdrShapeDefaults"),
        W("footnotePr"),
        W("endnotePr"),
        W("compat"),
        W("docVars"),
        W("rsids"),
        W("mathPr"),
        W("attachedSchema"),
        W("themeFontLang"),
        W("clrSchemeMapping"),
        W("doNotIncludeSubdocsInStats"),
        W("doNotAutoCompressPictures"),
        W("forceUpgrade"),
        W("captions"),
        W("readModeInkLockDown"),
        W("smartTagType"),
        W("schemaLibrary"),
        W("shapeDefaults"),
        W("doNotEmbedSmartTags"),
        W("decimalSymbol"),
        W("listSeparator"),
    ),
    W("footnotePr"): (
        W("pos"),
        W("numFmt"),
        W("numStart"),
        W("numRestart"),
        W("footnote"),
    ),
    W("tblStylePr"): (
        W("pPr"),
        W("rPr"),
        W("tblPr"),
        W("trPr"),
        W("tcPr"),
    ),
    W("pBdr"): (
        W("top"),
        W("left"),
        W("bottom"),
        W("right"),
        W("between"),
        W("bar"),
    ),
}


def _ordered_insert(parent: ET.Element, child: ET.Element) -> ET.Element:
    """Insert a schema-sequenced child without disturbing unknown extensions."""

    order = CHILD_ORDER.get(parent.tag)
    if order is None or child.tag not in order:
        parent.append(child)
        return child
    rank = {tag: index for index, tag in enumerate(order)}
    child_rank = rank[child.tag]
    for index, sibling in enumerate(parent):
        sibling_rank = rank.get(sibling.tag)
        if sibling_rank is not None and sibling_rank > child_rank:
            parent.insert(index, child)
            return child
    parent.append(child)
    return child


def _normalize_child_order(root: ET.Element) -> None:
    """Stably normalize every known OOXML sequence below *root*."""

    order = CHILD_ORDER.get(root.tag)
    if order is not None:
        rank = {tag: index for index, tag in enumerate(order)}
        children = list(root)
        ordered = sorted(
            (child for child in children if child.tag in rank),
            key=lambda child: rank[child.tag],
        )
        iterator = iter(ordered)
        normalized = [
            next(iterator) if child.tag in rank else child for child in children
        ]
        if normalized != children:
            root[:] = normalized
    for child in root:
        _normalize_child_order(child)


BODY_FONT = "EB Garamond"
SEMIBOLD_FONT = "EB Garamond SemiBold"
LANGUAGE = "en-GB-oxendict"

# Twentieths of a point unless otherwise noted.
BODY_SIZE = "30"  # half-points: 15 pt
BODY_LEADING = "386"  # 19.3 pt
BODY_INDENT = "300"  # 15 pt
NOTE_SIZE = "25"  # half-points: 12.5 pt
NOTE_LEADING = "320"  # 16 pt
NOTE_HANG = "375"  # 1.5 em at 12.5 pt
BLOCK_INDENT = "750"  # 2.5 em at 15 pt
BIBLIOGRAPHY_HANG = "450"  # 22.5 pt

# A4, with the PDF-led 140 x 227 mm type area.  The margin values are rounded
# to the nearest twip (1/1440 inch).
PAGE_WIDTH = "11906"
PAGE_HEIGHT = "16838"
INNER_MARGIN = "1323"  # 23.33 mm
OUTER_MARGIN = "2646"  # 46.67 mm
TOP_MARGIN = "1323"  # 23.33 mm
BOTTOM_MARGIN = "2646"  # 46.67 mm
FOOTER_DISTANCE = "567"  # 10 mm from the paper edge


FONT_FILES = OrderedDict(
    [
        ("regular", "EBGaramond-Regular.otf"),
        ("italic", "EBGaramond-Italic.otf"),
        ("bold", "EBGaramond-Bold.otf"),
        ("boldItalic", "EBGaramond-BoldItalic.otf"),
        ("semibold", "EBGaramond-SemiBold.otf"),
        ("semiboldItalic", "EBGaramond-SemiBoldItalic.otf"),
    ]
)

DEFAULT_FONT_DIRECTORY = Path("/usr/share/fonts/EBGaramond12-otf")
FONT_DIRECTORY_ENVIRONMENT = "LONGFORM_EB_GARAMOND_DIR"
FONT_EMBEDDING_ENVIRONMENT = "LONGFORM_EMBED_DOCX_FONTS"
FONT_SHA256 = {
    "EBGaramond-Regular.otf": (
        "a50199c0bd374344a11e3588c03beaac5404c768b6c29306d4af06aef91cf55a"
    ),
    "EBGaramond-Italic.otf": (
        "31f03b4e31c5eecfce383c49f66c592e061ddda394f4bb62de42a784cb59d95a"
    ),
    "EBGaramond-Bold.otf": (
        "2ff2454afe516643b51e68dc4738af04d27658a98943e5c91f261becbbf1773c"
    ),
    "EBGaramond-BoldItalic.otf": (
        "8c4c419dd617d74a433dbc723f765920fa414c6d94eb9bff3a1f5a749c4fb756"
    ),
    "EBGaramond-SemiBold.otf": (
        "7a4b8ee4ea0bc4856747788f9ef1db3595ea80a7bcaa7b28dc40e2e91c9721a7"
    ),
    "EBGaramond-SemiBoldItalic.otf": (
        "93c92e10d94b96d8e8e1378f2e1653999b2d60428c463cbe39e9b6b3f19f60f6"
    ),
}

FONT_RELATIONSHIP = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/font"
)
FONT_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.obfuscatedFont"
)
CANONICAL_KEYWORDS_PROPERTY = "LongformCanonicalKeywords"
CUSTOM_PROPERTY_FMTID = "{D5CDD505-2E9C-101B-9397-08002B2CF9AE}"


def _xml(data: bytes) -> ET.Element:
    return ET.fromstring(data)


def _xml_bytes(root: ET.Element) -> bytes:
    _normalize_child_order(root)
    return ET.tostring(
        root, encoding="UTF-8", xml_declaration=True, short_empty_elements=True
    )


def _find_or_add(parent: ET.Element, tag: str) -> ET.Element:
    child = parent.find(tag)
    if child is None:
        child = _ordered_insert(parent, ET.Element(tag))
    return child


def _replace_property(
    parent: ET.Element, tag: str, attributes: dict[str, str] | None = None
) -> ET.Element:
    for child in list(parent):
        if child.tag == tag:
            parent.remove(child)
    child = _ordered_insert(parent, ET.Element(tag))
    for name, value in (attributes or {}).items():
        child.set(W(name), value)
    return child


def _remove_properties(parent: ET.Element, *tags: str) -> None:
    wanted = {W(tag) for tag in tags}
    for child in list(parent):
        if child.tag in wanted:
            parent.remove(child)


def _style(styles: ET.Element, style_id: str) -> ET.Element | None:
    for item in styles.findall(W("style")):
        if item.get(W("styleId")) == style_id:
            return item
    return None


def _ensure_style(
    styles: ET.Element,
    style_id: str,
    name: str,
    style_type: str = "paragraph",
    based_on: str | None = None,
    next_style: str | None = None,
) -> ET.Element:
    item = _style(styles, style_id)
    if item is None:
        item = ET.SubElement(
            styles,
            W("style"),
            {W("type"): style_type, W("styleId"): style_id, W("customStyle"): "1"},
        )
        ET.SubElement(item, W("name"), {W("val"): name})
    else:
        name_node = _find_or_add(item, W("name"))
        name_node.set(W("val"), name)
    if based_on is not None:
        _replace_property(item, W("basedOn"), {"val": based_on})
    if next_style is not None:
        _replace_property(item, W("next"), {"val": next_style})
    if style_type == "paragraph" and item.find(W("qFormat")) is None:
        ET.SubElement(item, W("qFormat"))
    return item


def _configure_paragraph(
    style: ET.Element,
    *,
    before: str = "0",
    after: str = "0",
    line: str | None = BODY_LEADING,
    line_rule: str = "exact",
    left: str | None = None,
    right: str | None = None,
    first_line: str | None = None,
    hanging: str | None = None,
    alignment: str | None = None,
    keep_next: bool | None = None,
    keep_lines: bool | None = None,
    page_break_before: bool | None = None,
    outline_level: str | None = None,
    tab_position: str | None = None,
    bottom_border: bool = False,
) -> ET.Element:
    ppr = _find_or_add(style, W("pPr"))
    spacing = {"before": before, "after": after}
    if line is not None:
        spacing.update({"line": line, "lineRule": line_rule})
    _replace_property(ppr, W("spacing"), spacing)

    _remove_properties(ppr, "ind")
    if any(value is not None for value in (left, right, first_line, hanging)):
        attrs: dict[str, str] = {}
        if left is not None:
            attrs["left"] = left
        if right is not None:
            attrs["right"] = right
        if first_line is not None:
            attrs["firstLine"] = first_line
        if hanging is not None:
            attrs["hanging"] = hanging
        _replace_property(ppr, W("ind"), attrs)

    if alignment is not None:
        _replace_property(ppr, W("jc"), {"val": alignment})
    if keep_next is not None:
        _remove_properties(ppr, "keepNext")
        if keep_next:
            ET.SubElement(ppr, W("keepNext"))
    if keep_lines is not None:
        _remove_properties(ppr, "keepLines")
        if keep_lines:
            ET.SubElement(ppr, W("keepLines"))
    if page_break_before is not None:
        _remove_properties(ppr, "pageBreakBefore")
        if page_break_before:
            ET.SubElement(ppr, W("pageBreakBefore"))
    if outline_level is not None:
        _replace_property(ppr, W("outlineLvl"), {"val": outline_level})
    if tab_position is not None:
        tabs = _replace_property(ppr, W("tabs"))
        ET.SubElement(tabs, W("tab"), {W("val"): "left", W("pos"): tab_position})
    if bottom_border:
        borders = _replace_property(ppr, W("pBdr"))
        ET.SubElement(
            borders,
            W("bottom"),
            {
                W("val"): "single",
                W("sz"): "4",
                W("space"): "6",
                W("color"): "auto",
            },
        )
    else:
        _remove_properties(ppr, "pBdr")
    return ppr


def _configure_run(
    style: ET.Element,
    *,
    font: str = BODY_FONT,
    size: str = BODY_SIZE,
    italic: bool = False,
    bold: bool = False,
    underline: bool = False,
    superscript: bool = False,
    lining_tabular: bool = False,
) -> ET.Element:
    rpr = _find_or_add(style, W("rPr"))
    _replace_property(
        rpr,
        W("rFonts"),
        {"ascii": font, "hAnsi": font, "eastAsia": font, "cs": font},
    )
    _replace_property(rpr, W("sz"), {"val": size})
    _replace_property(rpr, W("szCs"), {"val": size})
    _replace_property(
        rpr,
        W("lang"),
        {"val": LANGUAGE, "eastAsia": "en-GB", "bidi": "ar-SA"},
    )
    _replace_property(rpr, W("color"), {"val": "000000"})
    _remove_properties(rpr, "b", "bCs", "i", "iCs", "u", "vertAlign")
    for tag in (W14("numForm"), W14("numSpacing")):
        for child in list(rpr):
            if child.tag == tag:
                rpr.remove(child)
    if bold:
        ET.SubElement(rpr, W("b"))
        ET.SubElement(rpr, W("bCs"))
    if italic:
        ET.SubElement(rpr, W("i"))
        ET.SubElement(rpr, W("iCs"))
    if underline:
        ET.SubElement(rpr, W("u"), {W("val"): "single"})
    if superscript:
        ET.SubElement(rpr, W("vertAlign"), {W("val"): "superscript"})
    if lining_tabular:
        ET.SubElement(rpr, W14("numForm"), {W14("val"): "lining"})
        ET.SubElement(rpr, W14("numSpacing"), {W14("val"): "tabular"})
    return rpr


def _configure_link_run(style: ET.Element, *, underline: bool) -> ET.Element:
    """Keep links visually discoverable without overriding contextual size.

    A link character style must inherit the 12.5-point note size inside notes
    and the 15-point body size elsewhere, so it intentionally specifies no
    face, size, language, weight, or posture.
    """

    rpr = _find_or_add(style, W("rPr"))
    _remove_properties(
        rpr,
        "rFonts",
        "sz",
        "szCs",
        "lang",
        "b",
        "bCs",
        "i",
        "iCs",
        "u",
        "vertAlign",
    )
    _replace_property(rpr, W("color"), {"val": "000000"})
    if underline:
        ET.SubElement(rpr, W("u"), {W("val"): "single"})
    return rpr


def _configure_note_label_styles(root: ET.Element) -> None:
    """Keep note-body marks full-size and on the baseline."""

    for style_id, name in (
        ("FootnoteLabel", "Footnote Label"),
        ("FootnoteCharacters", "Footnote Characters"),
        ("FootnoteCharactersuser", "Footnote Characters (user)"),
        ("Voetnoottekens", "Voetnoottekens"),
    ):
        label = _ensure_style(root, style_id, name, style_type="character")
        _configure_run(label, size=NOTE_SIZE)


def _configure_styles(data: bytes) -> bytes:
    root = _xml(data)

    defaults = _find_or_add(root, W("docDefaults"))
    rpr_default = _find_or_add(_find_or_add(defaults, W("rPrDefault")), W("rPr"))
    _replace_property(
        rpr_default,
        W("rFonts"),
        {"ascii": BODY_FONT, "hAnsi": BODY_FONT, "eastAsia": BODY_FONT, "cs": BODY_FONT},
    )
    _replace_property(rpr_default, W("sz"), {"val": BODY_SIZE})
    _replace_property(rpr_default, W("szCs"), {"val": BODY_SIZE})
    _replace_property(
        rpr_default,
        W("lang"),
        {"val": LANGUAGE, "eastAsia": "en-GB", "bidi": "ar-SA"},
    )

    normal = _ensure_style(root, "Normal", "Normal")
    _configure_paragraph(normal, after="0", alignment="both")
    _configure_run(normal)

    body = _ensure_style(root, "BodyText", "Body Text", based_on="Normal")
    _configure_paragraph(
        body,
        first_line=BODY_INDENT,
        alignment="both",
        keep_next=False,
    )
    body_ppr = _find_or_add(body, W("pPr"))
    _replace_property(body_ppr, W("widowControl"))
    _remove_properties(body_ppr, "suppressAutoHyphens")
    _configure_run(body)

    first = _ensure_style(
        root, "FirstParagraph", "First Paragraph", based_on="BodyText", next_style="BodyText"
    )
    _configure_paragraph(first, first_line="0", alignment="both", keep_next=False)
    _configure_run(first)

    for style_id, name in (("BlockText", "Block Text"), ("BlockQuotation", "Block Quotation")):
        block = _ensure_style(root, style_id, name, based_on="BodyText", next_style="BodyText")
        _configure_paragraph(
            block,
            before="193",
            after="193",
            left=BLOCK_INDENT,
            right=BLOCK_INDENT,
            first_line="0",
            alignment="both",
            keep_lines=True,
        )
        _configure_run(block)

    footnote = _ensure_style(root, "FootnoteText", "footnote text", based_on="Normal")
    _configure_paragraph(
        footnote,
        line=NOTE_LEADING,
        left=NOTE_HANG,
        hanging=NOTE_HANG,
        tab_position=NOTE_HANG,
        alignment="both",
    )
    _configure_run(footnote, size=NOTE_SIZE)

    footnote_reference = _ensure_style(
        root,
        "FootnoteReference",
        "footnote reference",
        style_type="character",
    )
    _configure_run(footnote_reference, size=BODY_SIZE, superscript=True)
    # LibreOffice serializes the note-body mark through one of these inherited
    # character-style IDs even when the source run used FootnoteLabel. Keep
    # those aliases metrically identical; the post-refresh stabilizer restores
    # Writer's built-in alias rewrite. The in-text call continues to use the
    # separate superscript FootnoteReference style.
    _configure_note_label_styles(root)

    bibliography = _ensure_style(
        root, "Bibliography", "Bibliography", based_on="BodyText"
    )
    _configure_paragraph(
        bibliography,
        after="60",
        left=BIBLIOGRAPHY_HANG,
        hanging=BIBLIOGRAPHY_HANG,
        alignment="both",
    )
    _configure_run(bibliography)

    heading_specs = (
        ("Heading1", "heading 1", "55", "630", "0", "483", "0"),
        ("Heading2", "heading 2", "41", "480", "579", "193", "1"),
        ("Heading3", "heading 3", "35", "410", "386", "97", "2"),
    )
    for style_id, name, size, line, before, after, level in heading_specs:
        heading = _ensure_style(
            root, style_id, name, based_on="Normal", next_style="FirstParagraph"
        )
        _configure_paragraph(
            heading,
            before=before,
            after=after,
            line=line,
            first_line="0",
            alignment="left",
            keep_next=True,
            keep_lines=True,
            page_break_before=False,
            outline_level=level,
        )
        _configure_run(heading, font=SEMIBOLD_FONT, size=size)

    title = _ensure_style(root, "Title", "Title", based_on="Normal", next_style="Subtitle")
    _configure_paragraph(
        title,
        before="1440",
        after="0",
        line="630",
        alignment="center",
        keep_next=True,
        keep_lines=True,
    )
    _configure_run(title, font=SEMIBOLD_FONT, size="55")

    subtitle = _ensure_style(
        root, "Subtitle", "Subtitle", based_on="Normal", next_style="Author"
    )
    _configure_paragraph(
        subtitle,
        before="0",
        after="720",
        line="420",
        alignment="center",
        keep_next=True,
        keep_lines=True,
    )
    _configure_run(subtitle, size="35", italic=True)

    author = _ensure_style(root, "Author", "Author", based_on="Normal", next_style="Date")
    _configure_paragraph(
        author,
        before="0",
        after="0",
        line="440",
        alignment="center",
        keep_next=True,
        keep_lines=True,
    )
    _configure_run(author, size="36")

    administrative = (
        ("StudentNumber", "Student Number", "Degree"),
        ("Degree", "Degree", "Supervisor"),
        ("Supervisor", "Supervisor", "Date"),
        ("Institute", "Institute", "BodyText"),
    )
    for style_id, name, next_style in administrative:
        # Academic fields are an independent optional feature. Refine its
        # markers only when its own DOCX processor has supplied the styles.
        item = _style(root, style_id)
        if item is None:
            continue
        _configure_paragraph(
            item,
            before="0",
            after="0",
            line=BODY_LEADING,
            alignment="center",
            keep_next=True,
            keep_lines=True,
        )
        _configure_run(item, lining_tabular=style_id == "StudentNumber")

    date = _ensure_style(root, "Date", "Date", based_on="Normal", next_style="BodyText")
    _configure_paragraph(
        date,
        before="386",
        after="0",
        line=BODY_LEADING,
        alignment="center",
        keep_next=True,
        keep_lines=True,
    )
    _configure_run(date)

    toc_heading = _ensure_style(
        root, "TOCHeading", "TOC Heading", based_on="Heading1", next_style="TOC1"
    )
    _configure_paragraph(
        toc_heading,
        before="0",
        after="483",
        line="630",
        alignment="left",
        keep_next=True,
        keep_lines=True,
        page_break_before=False,
        outline_level="9",
    )
    _configure_run(toc_heading, font=SEMIBOLD_FONT, size="55")

    toc1 = _ensure_style(root, "TOC1", "toc 1", based_on="BodyText")
    _configure_paragraph(toc1, first_line="0", alignment="left")
    toc1_ppr = _find_or_add(toc1, W("pPr"))
    tabs = _replace_property(toc1_ppr, W("tabs"))
    ET.SubElement(
        tabs,
        W("tab"),
        {W("val"): "right", W("pos"): "7937", W("leader"): "none"},
    )
    _configure_run(toc1)

    hyperlink = _ensure_style(
        root, "Hyperlink", "Hyperlink", style_type="character", based_on="BodyTextChar"
    )
    _configure_link_run(hyperlink, underline=True)
    citation_link = _ensure_style(
        root,
        "CitationLink",
        "Citation Link",
        style_type="character",
        based_on="BodyTextChar",
    )
    _configure_link_run(citation_link, underline=False)
    index_link = _ensure_style(
        root,
        "IndexLink",
        "Index Link",
        style_type="character",
        based_on="BodyTextChar",
    )
    _configure_link_run(index_link, underline=False)

    footer = _ensure_style(root, "Footer", "footer", based_on="Normal")
    _configure_paragraph(footer, line="320", alignment="left")
    _configure_run(footer, size=NOTE_SIZE)

    section_break = _ensure_style(
        root, "LongformSectionBreak", "Longform Section Break", based_on="Normal"
    )
    _configure_paragraph(section_break, line="1", line_rule="exact")
    _configure_run(section_break, size="2")
    section_rpr = _find_or_add(section_break, W("rPr"))
    _replace_property(section_rpr, W("vanish"))

    epigraph_widths = (("60", "1587"), ("75", "992"), ("Full", "0"))
    for suffix, indent in epigraph_widths:
        for front in (False, True):
            prefix = "FrontEpigraph" if front else "Epigraph"
            display_prefix = "Front Epigraph" if front else "Epigraph"
            text_id = f"{prefix}Text{suffix}"
            source_id = f"{prefix}Source{suffix}"
            text_name = f"{display_prefix} Text {suffix}"
            source_name = f"{display_prefix} Source {suffix}"
            # Epigraph is an independent optional feature. Refine only styles
            # already supplied by its feature-owned DOCX processor.
            text = _style(root, text_id)
            source = _style(root, source_id)
            if text is None or source is None:
                continue
            _configure_paragraph(
                text,
                before="1440" if front else "0",
                after="0",
                left=indent,
                right=indent,
                first_line="0",
                alignment="left",
                keep_next=True,
                keep_lines=True,
            )
            _configure_run(text)
            _configure_paragraph(
                source,
                before="193",
                after="193",
                left=indent,
                right=indent,
                first_line="0",
                alignment="right",
                keep_next=False,
                keep_lines=True,
            )
            _configure_run(source)

            if not front:
                separator_id = f"{source_id}Separator"
                separator_name = f"{source_name} Separator"
                separator = _style(root, separator_id)
                if separator is None:
                    continue
                _configure_paragraph(
                    separator,
                    before="193",
                    after="193",
                    left=indent,
                    right=indent,
                    first_line="0",
                    alignment="right",
                    keep_next=False,
                    keep_lines=True,
                    bottom_border=True,
                )
                _configure_run(separator)

    return _xml_bytes(root)


def _configure_settings(data: bytes) -> bytes:
    root = _xml(data)
    default_tab = _find_or_add(root, W("defaultTabStop"))
    default_tab.set(W("val"), NOTE_HANG)
    theme_language = _find_or_add(root, W("themeFontLang"))
    theme_language.set(W("val"), "en-GB")
    for tag in (
        W("mirrorMargins"),
        W("evenAndOddHeaders"),
        W("autoHyphenation"),
        W("updateFields"),
    ):
        child = _find_or_add(root, tag)
        child.set(W("val"), "true")
    hyphenation = _find_or_add(root, W("hyphenationZone"))
    hyphenation.set(W("val"), "240")
    for child in list(root):
        if child.tag == W("embedSystemFonts"):
            root.remove(child)
    return _xml_bytes(root)


def _configure_embedding_settings(data: bytes) -> bytes:
    root = _xml(data)
    for tag in (W("embedTrueTypeFonts"), W("saveSubsetFonts")):
        for child in list(root):
            if child.tag == tag:
                root.remove(child)
        if _font_embedding_requested():
            child = _find_or_add(root, tag)
            child.set(W("val"), "true")
    for child in list(root):
        if child.tag == W("embedSystemFonts"):
            root.remove(child)
    return _xml_bytes(root)


def _configure_sectpr(sectpr: ET.Element) -> None:
    page_size = _find_or_add(sectpr, W("pgSz"))
    page_size.set(W("w"), PAGE_WIDTH)
    page_size.set(W("h"), PAGE_HEIGHT)
    margins = _find_or_add(sectpr, W("pgMar"))
    for name, value in (
        ("top", TOP_MARGIN),
        ("right", OUTER_MARGIN),
        ("bottom", BOTTOM_MARGIN),
        ("left", INNER_MARGIN),
        ("header", "0"),
        ("footer", FOOTER_DISTANCE),
        ("gutter", "0"),
    ):
        margins.set(W(name), value)
    numbers = _find_or_add(sectpr, W("pgNumType"))
    numbers.set(W("fmt"), "decimal")
    numbers.attrib.pop(W("start"), None)
    _configure_section_footnotes(sectpr)
    _remove_properties(sectpr, "titlePg")


def _configure_section_footnotes(sectpr: ET.Element) -> None:
    """Apply note numbering without touching pagination geometry."""

    footnotes = _find_or_add(sectpr, W("footnotePr"))
    _replace_property(footnotes, W("numFmt"), {"val": "decimal"})
    _remove_properties(footnotes, "numStart")
    _replace_property(footnotes, W("numRestart"), {"val": "eachSect"})


def _configure_document_baseline(data: bytes) -> bytes:
    root = _xml(data)
    body = root.find(W("body"))
    if body is None:
        raise RuntimeError("DOCX document.xml has no body")
    sectpr = body.find(W("sectPr"))
    if sectpr is None:
        raise RuntimeError("DOCX document.xml has no final section properties")
    _configure_sectpr(sectpr)
    return _xml_bytes(root)


def _paragraph_style(paragraph: ET.Element) -> str | None:
    style = paragraph.find(f"./{W('pPr')}/{W('pStyle')}")
    return style.get(W("val")) if style is not None else None


def _paragraph_text(paragraph: ET.Element) -> str:
    return "".join(item.text or "" for item in paragraph.iter(W("t"))).strip()


def _core_keywords(data: bytes) -> str:
    root = _xml(data)
    node = root.find(CP("keywords"))
    value = "" if node is None else (node.text or "").strip()
    if not value:
        raise RuntimeError(
            "DOCX core metadata is missing keywords; set them in "
            "writing/manuscript/metadata.yml"
        )
    return value


def _stored_canonical_keywords(data: bytes, *, required: bool = False) -> str | None:
    root = _xml(data)
    for item in root.findall(CUSTOM("property")):
        if item.get("name") != CANONICAL_KEYWORDS_PROPERTY:
            continue
        value_node = next(iter(item), None)
        value = "" if value_node is None else (value_node.text or "").strip()
        if value:
            return value
        break
    if required:
        raise RuntimeError(
            "DOCX is missing its canonical keyword metadata anchor; run the "
            "DOCX prepare hook before refreshing the table of contents"
        )
    return None


def _store_canonical_keywords(data: bytes, value: str) -> bytes:
    """Persist keywords in a custom property that LibreOffice preserves.

    LibreOffice rewrites ``cp:keywords`` with its own delimiter conventions
    while refreshing the live TOC.  The custom property is package-local,
    deterministic, and lets the stabilizer restore the author-provided string
    exactly rather than trying to infer it from the rewritten value.
    """

    root = _xml(data)
    matches = [
        item
        for item in root.findall(CUSTOM("property"))
        if item.get("name") == CANONICAL_KEYWORDS_PROPERTY
    ]
    if matches:
        item = matches[0]
        for duplicate in matches[1:]:
            root.remove(duplicate)
    else:
        pids = []
        for property_node in root.findall(CUSTOM("property")):
            try:
                pids.append(int(property_node.get("pid", "")))
            except ValueError:
                continue
        item = ET.SubElement(
            root,
            CUSTOM("property"),
            {
                "fmtid": CUSTOM_PROPERTY_FMTID,
                "pid": str(max(pids, default=1) + 1),
                "name": CANONICAL_KEYWORDS_PROPERTY,
            },
        )
    item.set("fmtid", CUSTOM_PROPERTY_FMTID)
    for child in list(item):
        item.remove(child)
    text = ET.SubElement(item, VT("lpwstr"))
    text.text = value
    # Keep the package's conventional default namespace.  The downstream
    # metadata sanitizer deliberately matches unprefixed custom-property
    # elements when removing private bibliography and CSL paths.
    ET.register_namespace("", CUSTOM_PROPERTIES_NS)
    return _xml_bytes(root)


def _configure_core_properties(
    data: bytes, document_data: bytes, canonical_keywords: str | None = None
) -> bytes:
    """Complete DOCX identity metadata from semantic title-page fields.

    Pandoc intentionally keeps the visible title and subtitle separate, but
    its DOCX writer normally puts only the short title in dc:title.  The audit
    requires the full discovery title while retaining the composed title page,
    so derive dc:title from those two semantic paragraphs and fail closed when
    the remaining author-provided discovery fields were not carried through.
    """

    document = _xml(document_data)
    body = document.find(W("body"))
    if body is None:
        raise RuntimeError("DOCX document.xml has no body for core metadata")
    visible: dict[str, str] = {}
    for paragraph in body.findall(W("p")):
        style = _paragraph_style(paragraph)
        if style in {"Title", "Subtitle", "Author"} and style not in visible:
            visible[style] = _paragraph_text(paragraph)
    title = visible.get("Title", "")
    subtitle = visible.get("Subtitle", "")
    author = visible.get("Author", "")
    if not title or not author:
        raise RuntimeError("DOCX title and author paragraphs are required")
    full_title = f"{title}: {subtitle}" if subtitle else title

    root = _xml(data)

    def set_text(tag: str, value: str) -> None:
        node = root.find(tag)
        if node is None:
            node = ET.SubElement(root, tag)
        node.text = value

    set_text(DC("title"), full_title)
    set_text(DC("creator"), author)
    if canonical_keywords is not None:
        set_text(CP("keywords"), canonical_keywords)
    language = root.find(DC("language"))
    if language is None or not (language.text or "").strip():
        set_text(DC("language"), LANGUAGE)
    for tag, label in ((DC("subject"), "subject"), (CP("keywords"), "keywords")):
        node = root.find(tag)
        if node is None or not (node.text or "").strip():
            raise RuntimeError(
                f"DOCX core metadata is missing {label}; set it in "
                "writing/manuscript/metadata.yml"
            )
    return _xml_bytes(root)


def _set_run_style(run: ET.Element, style_id: str) -> None:
    rpr = run.find(W("rPr"))
    if rpr is None:
        rpr = ET.Element(W("rPr"))
        run.insert(0, rpr)
    _replace_property(rpr, W("rStyle"), {"val": style_id})


def _configure_links(root: ET.Element, footnotes: bool = False) -> None:
    def visit(element: ET.Element, paragraph_style: str | None = None, toc: bool = False) -> None:
        if element.tag == W("p"):
            paragraph_style = _paragraph_style(element)
            toc = toc or (paragraph_style or "").startswith("TOC")
        if element.tag == W("sdt"):
            gallery = element.find(f".//{W('docPartGallery')}")
            toc = toc or (
                gallery is not None and gallery.get(W("val")) == "Table of Contents"
            )
        if element.tag == W("hyperlink"):
            internal = element.get(W("anchor")) is not None
            quiet = footnotes or internal or paragraph_style == "Bibliography"
            style_id = "IndexLink" if toc else ("CitationLink" if quiet else "Hyperlink")
            for run in element.findall(f".//{W('r')}"):
                _set_run_style(run, style_id)
        for child in list(element):
            visit(child, paragraph_style, toc)

    visit(root)


def _configure_link_styles(data: bytes) -> bytes:
    root = _xml(data)
    hyperlink = _ensure_style(
        root, "Hyperlink", "Hyperlink", style_type="character", based_on="BodyTextChar"
    )
    _configure_link_run(hyperlink, underline=True)
    citation_link = _ensure_style(
        root,
        "CitationLink",
        "Citation Link",
        style_type="character",
        based_on="BodyTextChar",
    )
    _configure_link_run(citation_link, underline=False)
    index_link = _ensure_style(
        root,
        "IndexLink",
        "Index Link",
        style_type="character",
        based_on="BodyTextChar",
    )
    _configure_link_run(index_link, underline=False)
    return _xml_bytes(root)


def _configure_footnotes(data: bytes) -> bytes:
    root = _xml(data)
    for note in root.findall(W("footnote")):
        note_type = note.get(W("type"))
        if note_type in {"separator", "continuationSeparator"}:
            for child in list(note):
                note.remove(child)
            ET.SubElement(note, W("p"))
            continue
        for paragraph in note.findall(W("p")):
            ppr = paragraph.find(W("pPr"))
            if ppr is None:
                ppr = ET.Element(W("pPr"))
                paragraph.insert(0, ppr)
            _replace_property(ppr, W("pStyle"), {"val": "FootnoteText"})
            children = list(paragraph)
            label_index = None
            for index, child in enumerate(children):
                if child.tag == W("r") and child.find(W("footnoteRef")) is not None:
                    _set_run_style(child, "FootnoteLabel")
                    label_index = index
                    break
            if label_index is None:
                continue
            children = list(paragraph)
            next_index = label_index + 1
            if next_index < len(children) and children[next_index].tag == W("r"):
                candidate = children[next_index]
                texts = candidate.findall(W("t"))
                if texts and all((item.text or "").strip() == "" for item in texts):
                    for child in list(candidate):
                        if child.tag != W("rPr"):
                            candidate.remove(child)
                    ET.SubElement(candidate, W("tab"))
                    continue
                if candidate.find(W("tab")) is not None:
                    continue
            tab_run = ET.Element(W("r"))
            ET.SubElement(tab_run, W("tab"))
            paragraph.insert(next_index, tab_run)
    _configure_links(root, footnotes=True)
    return _xml_bytes(root)


def _page_field_footer(data: bytes, alignment: str) -> bytes:
    root = _xml(data)
    for child in list(root):
        root.remove(child)
    paragraph = ET.SubElement(root, W("p"))
    ppr = ET.SubElement(paragraph, W("pPr"))
    ET.SubElement(ppr, W("pStyle"), {W("val"): "Footer"})
    ET.SubElement(ppr, W("jc"), {W("val"): alignment})
    for field_type, instruction in (("begin", None), (None, " PAGE "), ("separate", None)):
        run = ET.SubElement(paragraph, W("r"))
        if instruction is not None:
            text = ET.SubElement(run, W("instrText"), {qn(XML_NS, "space"): "preserve"})
            text.text = instruction
        else:
            ET.SubElement(run, W("fldChar"), {W("fldCharType"): field_type})
    result = ET.SubElement(paragraph, W("r"))
    text = ET.SubElement(result, W("t"))
    text.text = "1"
    end = ET.SubElement(paragraph, W("r"))
    ET.SubElement(end, W("fldChar"), {W("fldCharType"): "end"})
    return _xml_bytes(root)


def _relationship_targets(data: bytes) -> dict[str, str]:
    root = _xml(data)
    return {
        item.get("Id", ""): item.get("Target", "")
        for item in root.findall(REL("Relationship"))
    }


def _configure_footers(parts: dict[str, bytes]) -> None:
    document = _xml(parts["word/document.xml"])
    body = document.find(W("body"))
    sectpr = body.find(W("sectPr")) if body is not None else None
    if sectpr is None:
        raise RuntimeError("DOCX has no final section for footer configuration")
    relationships = _relationship_targets(parts["word/_rels/document.xml.rels"])
    for reference in sectpr.findall(W("footerReference")):
        target = relationships.get(reference.get(R("id"), ""))
        if not target:
            continue
        part_name = "word/" + target.lstrip("/")
        if part_name not in parts:
            continue
        reference_type = reference.get(W("type"), "default")
        alignment = "left" if reference_type == "even" else "right"
        parts[part_name] = _page_field_footer(parts[part_name], alignment)


def _font_embedding_allowed(data: bytes, filename: str) -> None:
    if len(data) < 12:
        raise RuntimeError(f"font is not a valid OpenType file: {filename}")
    table_count = struct.unpack(">H", data[4:6])[0]
    os2_offset = None
    for index in range(table_count):
        position = 12 + index * 16
        if position + 16 > len(data):
            break
        tag, _, offset, length = struct.unpack(">4sIII", data[position : position + 16])
        if tag == b"OS/2" and offset + min(length, 10) <= len(data):
            os2_offset = offset
            break
    if os2_offset is None:
        raise RuntimeError(f"font has no OS/2 embedding permissions: {filename}")
    fs_type = struct.unpack(">H", data[os2_offset + 8 : os2_offset + 10])[0]
    if fs_type & 0x0002 or fs_type & 0x0200:
        raise RuntimeError(
            f"font licensing bits prohibit editable DOCX embedding: {filename}"
        )


def _font_key(data: bytes) -> tuple[str, bytes]:
    digest = hashlib.sha256(data).digest()
    key_uuid = uuid.UUID(bytes=digest[:16])
    key = "{" + str(key_uuid).upper() + "}"
    key_bytes = key_uuid.bytes_le
    obfuscated = bytearray(data)
    for index in range(min(32, len(obfuscated))):
        obfuscated[index] ^= key_bytes[index % 16]
    return key, bytes(obfuscated)


def _font_directory() -> Path:
    configured = os.environ.get(FONT_DIRECTORY_ENVIRONMENT)
    if configured:
        path = Path(configured)
        if not path.is_absolute():
            raise RuntimeError(
                f"{FONT_DIRECTORY_ENVIRONMENT} must be an absolute path: {path}"
            )
        return path
    return DEFAULT_FONT_DIRECTORY


def _load_fonts() -> dict[str, tuple[str, bytes, str]]:
    font_dir = _font_directory()
    if not font_dir.is_dir():
        raise RuntimeError(
            "EB Garamond font directory is missing: "
            f"{font_dir}. Install the 1.001 OTF family there or set "
            f"{FONT_DIRECTORY_ENVIRONMENT} to its absolute directory."
        )
    loaded: dict[str, tuple[str, bytes, str]] = {}
    for role, filename in FONT_FILES.items():
        path = font_dir / filename
        if not path.is_file():
            raise RuntimeError(f"required EB Garamond font is missing: {path}")
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        expected = FONT_SHA256[filename]
        if digest != expected:
            raise RuntimeError(
                "installed EB Garamond font has an unexpected checksum: "
                f"{path} (expected {expected}, found {digest})"
            )
        _font_embedding_allowed(data, filename)
        key, obfuscated = _font_key(data)
        loaded[role] = (key, obfuscated, filename)
    return loaded


def _strip_embedded_fonts(parts: dict[str, bytes]) -> None:
    """Remove font payloads while retaining font names and document styles."""

    for name in list(parts):
        if name.startswith("word/fonts/") and name.lower().endswith(".odttf"):
            del parts[name]

    font_table_name = "word/fontTable.xml"
    if font_table_name in parts:
        font_table = _xml(parts[font_table_name])
        for font in font_table.findall(W("font")):
            for child in list(font):
                if child.tag in {
                    W("embedRegular"),
                    W("embedItalic"),
                    W("embedBold"),
                    W("embedBoldItalic"),
                }:
                    font.remove(child)
        parts[font_table_name] = _xml_bytes(font_table)

    relationships_name = "word/_rels/fontTable.xml.rels"
    if relationships_name in parts:
        relationships = _xml(parts[relationships_name])
        for relationship in list(relationships):
            if relationship.get("Type") == FONT_RELATIONSHIP:
                relationships.remove(relationship)
        if list(relationships):
            ET.register_namespace("", REL_NS)
            parts[relationships_name] = _xml_bytes(relationships)
        else:
            del parts[relationships_name]

    content_types = _xml(parts["[Content_Types].xml"])
    for item in list(content_types.findall(CT("Default"))):
        if item.get("Extension", "").lower() == "odttf":
            content_types.remove(item)
    ET.register_namespace("", CT_NS)
    parts["[Content_Types].xml"] = _xml_bytes(content_types)


def _configure_content_types(data: bytes) -> bytes:
    root = _xml(data)
    existing = [
        item
        for item in root.findall(CT("Default"))
        if item.get("Extension", "").lower() == "odttf"
    ]
    if (
        len(existing) == 1
        and existing[0].get("ContentType") == FONT_CONTENT_TYPE
    ):
        return data
    if existing:
        existing[0].set("ContentType", FONT_CONTENT_TYPE)
        for duplicate in existing[1:]:
            root.remove(duplicate)
    else:
        ET.SubElement(
            root,
            CT("Default"),
            {"Extension": "odttf", "ContentType": FONT_CONTENT_TYPE},
        )
    # Some office readers require the package content-types namespace to be
    # the default namespace, despite namespace prefixes being XML-equivalent.
    ET.register_namespace("", CT_NS)
    return _xml_bytes(root)


def _configure_font_table(
    data: bytes, fonts: dict[str, tuple[str, bytes, str]]
) -> tuple[bytes, bytes, dict[str, bytes]]:
    root = _xml(data)
    relationships = ET.Element(REL("Relationships"))
    font_parts: dict[str, bytes] = {}

    relation_ids: dict[str, str] = {}
    for index, (role, (key, obfuscated, filename)) in enumerate(fonts.items(), 1):
        relation_id = f"rIdLongformFont{index}"
        relation_ids[role] = relation_id
        output_name = Path(filename).with_suffix(".odttf").name
        ET.SubElement(
            relationships,
            REL("Relationship"),
            {
                "Id": relation_id,
                "Type": FONT_RELATIONSHIP,
                "Target": f"fonts/{output_name}",
            },
        )
        font_parts[f"word/fonts/{output_name}"] = obfuscated

    for name in (BODY_FONT, SEMIBOLD_FONT):
        for item in list(root.findall(W("font"))):
            if item.get(W("name")) == name:
                root.remove(item)
    body = ET.SubElement(root, W("font"), {W("name"): BODY_FONT})
    ET.SubElement(body, W("family"), {W("val"): "roman"})
    ET.SubElement(body, W("pitch"), {W("val"): "variable"})
    for tag, role in (
        ("embedRegular", "regular"),
        ("embedItalic", "italic"),
        ("embedBold", "bold"),
        ("embedBoldItalic", "boldItalic"),
    ):
        ET.SubElement(
            body,
            W(tag),
            {
                R("id"): relation_ids[role],
                W("fontKey"): fonts[role][0],
                W("subsetted"): "false",
            },
        )
    semibold = ET.SubElement(root, W("font"), {W("name"): SEMIBOLD_FONT})
    ET.SubElement(semibold, W("family"), {W("val"): "roman"})
    ET.SubElement(semibold, W("pitch"), {W("val"): "variable"})
    for tag, role in (("embedRegular", "semibold"), ("embedItalic", "semiboldItalic")):
        ET.SubElement(
            semibold,
            W(tag),
            {
                R("id"): relation_ids[role],
                W("fontKey"): fonts[role][0],
                W("subsetted"): "false",
            },
        )
    ET.register_namespace("", REL_NS)
    return _xml_bytes(root), _xml_bytes(relationships), font_parts


def _embed_fonts(parts: dict[str, bytes]) -> None:
    fonts = _load_fonts()
    for name in list(parts):
        if name.startswith("word/fonts/") and name.lower().endswith(".odttf"):
            del parts[name]
    font_table, relationships, font_parts = _configure_font_table(
        parts["word/fontTable.xml"], fonts
    )
    parts["word/fontTable.xml"] = font_table
    parts["word/_rels/fontTable.xml.rels"] = relationships
    parts.update(font_parts)
    parts["[Content_Types].xml"] = _configure_content_types(
        parts["[Content_Types].xml"]
    )


def _font_embedding_requested() -> bool:
    value = os.environ.get(FONT_EMBEDDING_ENVIRONMENT, "0")
    if value not in {"0", "1"}:
        raise RuntimeError(
            f"{FONT_EMBEDDING_ENVIRONMENT} must be 0 or 1, found {value!r}"
        )
    return value == "1"


def _apply_font_embedding_policy(parts: dict[str, bytes]) -> None:
    if _font_embedding_requested():
        _embed_fonts(parts)
    else:
        _strip_embedded_fonts(parts)


def _copy_section(
    base: ET.Element, *, footer: bool, break_type: str = "oddPage"
) -> ET.Element:
    section = deepcopy(base)
    _configure_sectpr(section)
    _replace_property(section, W("type"), {"val": break_type})
    if not footer:
        for reference in list(section.findall(W("footerReference"))):
            section.remove(reference)
        for reference in list(section.findall(W("headerReference"))):
            section.remove(reference)
    return section


def _section_paragraph(section: ET.Element) -> ET.Element:
    paragraph = ET.Element(W("p"))
    ppr = ET.SubElement(paragraph, W("pPr"))
    ET.SubElement(ppr, W("pStyle"), {W("val"): "LongformSectionBreak"})
    ppr.append(section)
    return paragraph


def _configure_generated_document(data: bytes) -> bytes:
    root = _xml(data)
    body = root.find(W("body"))
    if body is None:
        raise RuntimeError("DOCX document.xml has no body")
    final_section = body.find(W("sectPr"))
    if final_section is None:
        raise RuntimeError("DOCX document.xml has no final section properties")
    _configure_sectpr(final_section)
    # In WordprocessingML the break type stored in a section's terminal
    # sectPr describes how the following section begins.
    _replace_property(final_section, W("type"), {"val": "oddPage"})

    # Remove only our own generated section-break paragraphs before rebuilding
    # the sequence.  This makes prepare -> stabilize and repeated invocations
    # byte-idempotent without disturbing author content.
    for child in list(body):
        if child.tag == W("p") and _paragraph_style(child) == "LongformSectionBreak":
            body.remove(child)

    front_source = next(
        (
            child
            for child in list(body)
            if child.tag == W("p")
            and (_paragraph_style(child) or "").startswith("FrontEpigraphSource")
        ),
        None,
    )
    if front_source is not None:
        front_index = list(body).index(front_source)
        body.insert(
            front_index + 1,
            _section_paragraph(_copy_section(final_section, footer=False)),
        )

    headings = [
        child
        for child in list(body)
        if child.tag == W("p") and _paragraph_style(child) == "Heading1"
    ]
    for heading_index, heading in enumerate(headings):
        index = list(body).index(heading)
        # Without a front-epigraph marker, the first break terminates title
        # matter and therefore carries no folio. Later breaks terminate body
        # sections and retain the publication footer.
        footer = front_source is not None or heading_index > 0
        body.insert(
            index,
            _section_paragraph(_copy_section(final_section, footer=footer)),
        )

    _configure_links(root)
    return _xml_bytes(root)


def _style_from_root(styles: ET.Element, style_id: str) -> ET.Element:
    item = _style(styles, style_id)
    if item is None:
        raise RuntimeError(f"DOCX layout drift: missing style {style_id}")
    return item


def _require_word_attribute(
    parent: ET.Element,
    path: str,
    attribute: str,
    expected: str,
    label: str,
) -> ET.Element:
    node = parent.find(path)
    actual = None if node is None else node.get(W(attribute))
    if actual != expected:
        raise RuntimeError(
            f"DOCX layout drift in {label}: expected {expected}, found {actual}"
        )
    return node


def _require_word_true(parent: ET.Element, path: str, label: str) -> ET.Element:
    node = parent.find(path)
    if node is None or node.get(W("val")) not in {None, "true", "1", "on"}:
        actual = None if node is None else node.get(W("val"))
        raise RuntimeError(
            f"DOCX layout drift in {label}: expected true, found {actual}"
        )
    return node


def _require_indent(
    style: ET.Element, side: str, expected: str, label: str
) -> None:
    indent = style.find(f"./{W('pPr')}/{W('ind')}")
    if indent is None:
        raise RuntimeError(f"DOCX layout drift in {label}: missing indentation")
    alternatives = (side, "start" if side == "left" else "end")
    if not any(indent.get(W(name)) == expected for name in alternatives):
        raise RuntimeError(
            f"DOCX layout drift in {label}: expected {side}={expected}"
        )


def _note_label_state(styles: ET.Element, style_id: str) -> tuple[str | None, str | None]:
    style = _style_from_root(styles, style_id)
    size = style.find(f"./{W('rPr')}/{W('sz')}")
    vertical = style.find(f"./{W('rPr')}/{W('vertAlign')}")
    return (
        None if size is None else size.get(W("val")),
        None if vertical is None else vertical.get(W("val")),
    )


def _validate_footnote_content(data: bytes, *, allow_separator_rules: bool) -> None:
    footnotes = _xml(data)
    for footnote in footnotes.findall(W("footnote")):
        note_type = footnote.get(W("type"))
        if note_type in {"separator", "continuationSeparator"}:
            if not allow_separator_rules and (
                footnote.find(f".//{W('separator')}") is not None
                or footnote.find(f".//{W('continuationSeparator')}") is not None
            ):
                raise RuntimeError("DOCX layout drift: footnote rule was restored")
            continue
        for paragraph in footnote.findall(W("p")):
            if _paragraph_style(paragraph) != "FootnoteText":
                raise RuntimeError("DOCX layout drift: note paragraph style changed")
            reference = paragraph.find(
                f".//{W('footnoteRef')}/../{W('rPr')}/{W('rStyle')}"
            )
            if reference is None or reference.get(W("val")) not in {
                "FootnoteLabel",
                "FootnoteCharacters",
                "FootnoteCharactersuser",
                "Voetnoottekens",
            }:
                raise RuntimeError("DOCX layout drift: note label style changed")
            if len(paragraph.findall(f".//{W('tab')}")) != 1:
                raise RuntimeError("DOCX layout drift: note label tab changed")


def _validate_known_toc_rewrites(parts: dict[str, bytes]) -> None:
    """Accept only the narrow presentation rewrites made by LibreOffice.

    Writer maps note marks to its built-in superscript alias, removes
    section-local note restart declarations, and restores separator glyphs.
    The typography-owned stabilizer repairs those fields after TOC refresh;
    every other layout property remains subject to the strict final check.
    """

    styles = _xml(parts["word/styles.xml"])
    expected = (NOTE_SIZE, None)
    expected_with_baseline = {expected, (NOTE_SIZE, "baseline")}
    for style_id in ("FootnoteLabel", "FootnoteCharactersuser", "Voetnoottekens"):
        if _note_label_state(styles, style_id) not in expected_with_baseline:
            raise RuntimeError(f"DOCX layout drift in {style_id}")
    characters_state = _note_label_state(styles, "FootnoteCharacters")
    if characters_state not in expected_with_baseline | {("30", "superscript")}:
        raise RuntimeError("DOCX layout drift in FootnoteCharacters")

    document = _xml(parts["word/document.xml"])
    for index, section in enumerate(document.findall(f".//{W('sectPr')}"), 1):
        footnote_properties = section.find(W("footnotePr"))
        if footnote_properties is None:
            continue
        _require_word_attribute(
            footnote_properties,
            f"./{W('numFmt')}",
            "val",
            "decimal",
            f"section {index} footnote number format",
        )
        _require_word_attribute(
            footnote_properties,
            f"./{W('numRestart')}",
            "val",
            "eachSect",
            f"section {index} footnote restart",
        )
        if footnote_properties.find(W("numStart")) is not None:
            raise RuntimeError(
                f"DOCX layout drift: section {index} footnotes no longer start at 1"
            )

    _validate_footnote_content(
        parts["word/footnotes.xml"], allow_separator_rules=True
    )


def _restore_known_toc_rewrites(parts: dict[str, bytes]) -> None:
    """Restore typography-owned note policy without changing page geometry."""

    styles = _xml(parts["word/styles.xml"])
    _configure_note_label_styles(styles)
    parts["word/styles.xml"] = _xml_bytes(styles)

    document = _xml(parts["word/document.xml"])
    for section in document.findall(f".//{W('sectPr')}"):
        _configure_section_footnotes(section)
    parts["word/document.xml"] = _xml_bytes(document)

    parts["word/footnotes.xml"] = _configure_footnotes(
        parts["word/footnotes.xml"]
    )


def _validate_layout(parts: dict[str, bytes]) -> None:
    """Fail if a TOC refresh changed any pagination-sensitive property."""

    styles = _xml(parts["word/styles.xml"])
    body = _style_from_root(styles, "BodyText")
    _require_word_attribute(body, f"./{W('rPr')}/{W('sz')}", "val", "30", "body size")
    _require_word_attribute(
        body, f"./{W('pPr')}/{W('spacing')}", "line", "386", "body leading"
    )
    _require_word_attribute(
        body,
        f"./{W('pPr')}/{W('spacing')}",
        "lineRule",
        "exact",
        "body leading rule",
    )
    _require_word_attribute(
        body, f"./{W('pPr')}/{W('ind')}", "firstLine", "300", "body indent"
    )

    block = _style_from_root(styles, "BlockText")
    _require_indent(block, "left", "750", "quotation left indent")
    _require_indent(block, "right", "750", "quotation right indent")

    note = _style_from_root(styles, "FootnoteText")
    _require_word_attribute(note, f"./{W('rPr')}/{W('sz')}", "val", "25", "note size")
    _require_word_attribute(
        note, f"./{W('pPr')}/{W('spacing')}", "line", "320", "note leading"
    )
    _require_word_attribute(
        note, f"./{W('pPr')}/{W('ind')}", "hanging", "375", "note hang"
    )
    _require_word_attribute(
        note,
        f"./{W('pPr')}/{W('tabs')}/{W('tab')}",
        "pos",
        "375",
        "note label tab",
    )
    for style_id in (
        "FootnoteLabel",
        "FootnoteCharacters",
        "FootnoteCharactersuser",
        "Voetnoottekens",
    ):
        label_style = _style_from_root(styles, style_id)
        _require_word_attribute(
            label_style,
            f"./{W('rPr')}/{W('sz')}",
            "val",
            NOTE_SIZE,
            f"{style_id} size",
        )
        vertical = label_style.find(f"./{W('rPr')}/{W('vertAlign')}")
        if vertical is not None and vertical.get(W("val")) != "baseline":
            raise RuntimeError(
                f"DOCX layout drift: {style_id} became superscript"
            )

    bibliography = _style_from_root(styles, "Bibliography")
    _require_word_attribute(
        bibliography,
        f"./{W('pPr')}/{W('ind')}",
        "hanging",
        "450",
        "bibliography hang",
    )
    _require_word_attribute(
        bibliography,
        f"./{W('pPr')}/{W('spacing')}",
        "after",
        "60",
        "bibliography entry spacing",
    )

    for style_id, size, line in (
        ("Heading1", "55", "630"),
        ("Heading2", "41", "480"),
        ("Heading3", "35", "410"),
    ):
        heading = _style_from_root(styles, style_id)
        _require_word_attribute(
            heading,
            f"./{W('rPr')}/{W('rFonts')}",
            "ascii",
            SEMIBOLD_FONT,
            f"{style_id} face",
        )
        _require_word_attribute(
            heading, f"./{W('rPr')}/{W('sz')}", "val", size, f"{style_id} size"
        )
        _require_word_attribute(
            heading,
            f"./{W('pPr')}/{W('spacing')}",
            "line",
            line,
            f"{style_id} leading",
        )
        if heading.find(f"./{W('pPr')}/{W('keepNext')}") is None:
            raise RuntimeError(f"DOCX layout drift: {style_id} lost keep-with-next")

    settings = _xml(parts["word/settings.xml"])
    _require_word_attribute(
        settings,
        f"./{W('defaultTabStop')}",
        "val",
        NOTE_HANG,
        "default tab stop",
    )
    _require_word_attribute(
        settings,
        f"./{W('themeFontLang')}",
        "val",
        "en-GB",
        "theme font language",
    )
    for tag in ("mirrorMargins", "evenAndOddHeaders"):
        _require_word_true(settings, f"./{W(tag)}", f"setting {tag}")
    document = _xml(parts["word/document.xml"])
    document_body = document.find(W("body"))
    if document_body is None:
        raise RuntimeError("DOCX layout drift: document body is missing")
    headings = [
        item
        for item in document_body.findall(W("p"))
        if _paragraph_style(item) == "Heading1"
    ]
    sections = document_body.findall(f".//{W('sectPr')}")
    front_sources = [
        item
        for item in document_body.findall(W("p"))
        if (_paragraph_style(item) or "").startswith("FrontEpigraphSource")
    ]
    if len(front_sources) > 1:
        raise RuntimeError("DOCX layout drift: multiple front epigraph markers")
    expected_section_count = 1 + len(headings) + len(front_sources)
    if len(sections) != expected_section_count:
        raise RuntimeError(
            "DOCX layout drift: expected "
            f"{expected_section_count} derived sections, found {len(sections)}"
        )
    for index, section in enumerate(sections):
        _require_word_attribute(
            section, f"./{W('type')}", "val", "oddPage", f"section {index + 1}"
        )
        numbers = _require_word_attribute(
            section,
            f"./{W('pgNumType')}",
            "fmt",
            "decimal",
            f"section {index + 1} numbering",
        )
        if numbers.get(W("start")) is not None:
            raise RuntimeError("DOCX layout drift: page numbering was restarted")
        footnote_properties = section.find(W("footnotePr"))
        if footnote_properties is None:
            raise RuntimeError(
                f"DOCX layout drift: section {index + 1} footnote settings are missing"
            )
        _require_word_attribute(
            footnote_properties,
            f"./{W('numFmt')}",
            "val",
            "decimal",
            f"section {index + 1} footnote number format",
        )
        _require_word_attribute(
            footnote_properties,
            f"./{W('numRestart')}",
            "val",
            "eachSect",
            f"section {index + 1} footnote restart",
        )
        if footnote_properties.find(W("numStart")) is not None:
            raise RuntimeError(
                f"DOCX layout drift: section {index + 1} footnotes no longer start at 1"
            )
        margins = section.find(W("pgMar"))
        expected_margins = {
            "top": TOP_MARGIN,
            "right": OUTER_MARGIN,
            "bottom": BOTTOM_MARGIN,
            "left": INNER_MARGIN,
        }
        if margins is None or any(
            margins.get(W(name)) != value for name, value in expected_margins.items()
        ):
            raise RuntimeError(
                f"DOCX layout drift: section {index + 1} margins changed"
            )
        footer_types = {
            item.get(W("type")) for item in section.findall(W("footerReference"))
        }
        # Preliminary sections may deliberately hide folios. LibreOffice may
        # drop an unused first-page reference; the remaining combinations are
        # the portable states generated by the preparation pass.
        footer_valid = footer_types in (
            set(),
            {"even", "default"},
            {"even", "default", "first"},
        )
        if not footer_valid:
            raise RuntimeError(
                f"DOCX layout drift: section {index + 1} footer visibility changed"
            )

    title_order = [
        _paragraph_style(item)
        for item in document_body.findall(W("p"))
        if _paragraph_style(item)
        in {
            "Title",
            "Subtitle",
            "Author",
            "StudentNumber",
            "Degree",
            "Supervisor",
            "Date",
            "Institute",
        }
    ]
    canonical_title_order = [
        "Title", "Subtitle", "Author", "StudentNumber", "Degree",
        "Supervisor", "Date", "Institute",
    ]
    expected_title_order = [
        style for style in canonical_title_order if style in title_order
    ]
    if len(title_order) != len(set(title_order)) or title_order != expected_title_order:
        raise RuntimeError("DOCX layout drift: title fields changed or moved")

    _validate_footnote_content(
        parts["word/footnotes.xml"], allow_separator_rules=False
    )


def configure_reference(source: Path, output: Path) -> None:
    package = DocxPackage(source)
    parts = package.parts
    parts["word/styles.xml"] = _configure_styles(parts["word/styles.xml"])
    parts["word/settings.xml"] = _configure_embedding_settings(
        _configure_settings(parts["word/settings.xml"])
    )
    parts["word/document.xml"] = _configure_document_baseline(
        parts["word/document.xml"]
    )
    parts["word/footnotes.xml"] = _configure_footnotes(parts["word/footnotes.xml"])
    _configure_footers(parts)
    _strip_embedded_fonts(parts)
    package.write(output)


def configure_generated(path: Path) -> None:
    package = DocxPackage(path)
    parts = package.parts
    parts["word/styles.xml"] = _configure_styles(parts["word/styles.xml"])
    parts["word/settings.xml"] = _configure_embedding_settings(
        _configure_settings(parts["word/settings.xml"])
    )
    parts["word/document.xml"] = _configure_generated_document(
        parts["word/document.xml"]
    )
    canonical_keywords = _stored_canonical_keywords(
        parts["docProps/custom.xml"]
    ) or _core_keywords(parts["docProps/core.xml"])
    parts["docProps/custom.xml"] = _store_canonical_keywords(
        parts["docProps/custom.xml"], canonical_keywords
    )
    parts["docProps/core.xml"] = _configure_core_properties(
        parts["docProps/core.xml"],
        parts["word/document.xml"],
        canonical_keywords,
    )
    parts["word/footnotes.xml"] = _configure_footnotes(parts["word/footnotes.xml"])
    _configure_footers(parts)
    _apply_font_embedding_policy(parts)
    package.write(path)


def stabilize_generated(path: Path) -> None:
    """Restore deterministic package data after an optional TOC refresh.

    LibreOffice has three known note-related OOXML rewrites that do not alter
    pagination under the feature's exact note leading and fixed label tab.
    Those are checked and restored first. Any other metric, margin, section,
    or content drift still fails instead of being corrected behind stale page
    numbers.
    """

    package = DocxPackage(path)
    parts = package.parts
    _validate_known_toc_rewrites(parts)
    _restore_known_toc_rewrites(parts)
    _validate_layout(parts)

    document = _xml(parts["word/document.xml"])
    _configure_links(document)
    parts["word/document.xml"] = _xml_bytes(document)

    footnotes = _xml(parts["word/footnotes.xml"])
    _configure_links(footnotes, footnotes=True)
    parts["word/footnotes.xml"] = _xml_bytes(footnotes)

    parts["word/styles.xml"] = _configure_link_styles(parts["word/styles.xml"])
    parts["word/settings.xml"] = _configure_embedding_settings(
        parts["word/settings.xml"]
    )
    canonical_keywords = _stored_canonical_keywords(
        parts["docProps/custom.xml"], required=True
    )
    parts["docProps/core.xml"] = _configure_core_properties(
        parts["docProps/core.xml"],
        parts["word/document.xml"],
        canonical_keywords,
    )
    _apply_font_embedding_policy(parts)
    package.write(path)
