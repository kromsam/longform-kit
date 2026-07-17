#!/usr/bin/env python3
"""Build and inspect every public Longform Kit output in a disposable copy."""

from __future__ import annotations

import base64
import difflib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import xml.etree.ElementTree as ET
from zipfile import BadZipFile, ZipFile


ROOT = Path(__file__).resolve().parents[1]
QUARTO = os.environ.get("QUARTO", "quarto")
LIBRARY = (ROOT / "tests/fixtures/references/library.json").resolve()
STYLE = (ROOT / "tests/fixtures/references/longform-test-note.csl").resolve()
WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

INTRO_MARKER = "Integration fixture: the first chapter is present."
CONCLUSION_MARKER = "Integration fixture: the final chapter is present."
GFM_MARKER = "Integration fixture: this sentence belongs only in GFM."
PAGINATED_MARKER = (
    "Integration fixture: this sentence belongs only in paginated output."
)
FIGURE_ALT = "Integration fixture figure"
ONE_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def fail(message: str) -> None:
    raise AssertionError(message)


def progress(message: str) -> None:
    print(f"test_build: {message}", flush=True)


def run(
    *command: str,
    cwd: Path,
    capture: bool = True,
) -> str:
    """Run a command and include its complete output in any failure."""
    log = None if capture else tempfile.TemporaryFile(mode="w+t", encoding="utf-8")
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            stdout=subprocess.PIPE if capture else log,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if capture:
            output = result.stdout or ""
        else:
            assert log is not None
            log.flush()
            log.seek(0)
            output = log.read()
    finally:
        if log is not None:
            log.close()
    if result.returncode != 0:
        fail(f"command failed ({result.returncode}): {' '.join(command)}\n{output}")
    return output


def require_tools() -> None:
    for command in (QUARTO, "git", "pdfinfo", "pdftotext"):
        if shutil.which(command) is None:
            fail(f"missing required command: {command}")
    for path in (LIBRARY, STYLE):
        if not path.is_file():
            fail(f"missing committed test fixture: {path.relative_to(ROOT)}")


def copy_project(destination: Path) -> None:
    """Copy tracked project material without local state or build products."""

    def ignore(directory: str, names: list[str]) -> set[str]:
        current = Path(directory).resolve()
        ignored = {
            name
            for name in names
            if name in {".quarto", "__pycache__"} or name.endswith(".pyc")
        }
        if current == ROOT:
            ignored.update(
                name
                for name in names
                if name
                in {
                    ".git",
                    ".cache",
                    "build",
                    "_quarto.yml.local",
                    "index.pdf",
                    "index.tex",
                    ".DS_Store",
                }
            )
            ignored.update(name for name in names if name.endswith("_files"))
        elif current == ROOT / "references":
            ignored.update(
                name
                for name in names
                if name
                in {
                    "library.json",
                    "style.csl",
                    "zotero-styles",
                    ".csl-parents",
                }
            )
        elif current == ROOT / "document":
            ignored.update(name for name in names if name == ".ztr-directory")
        return ignored

    shutil.copytree(ROOT, destination, ignore=ignore)


def write_local_configuration(project: Path) -> None:
    # JSON strings are valid YAML scalars and safely preserve spaces in paths.
    (project / "_quarto.yml.local").write_text(
        f"bibliography: {json.dumps(str(LIBRARY))}\n"
        f"csl: {json.dumps(str(STYLE))}\n",
        encoding="utf-8",
    )


def add_test_manuscript_content(project: Path) -> None:
    introduction = project / "document/manuscript/01-introduction.md"
    conclusion = project / "document/manuscript/02-conclusion.md"
    figure = project / "resources/integration-fixture.png"
    figure.parent.mkdir(exist_ok=True)
    figure.write_bytes(ONE_PIXEL_PNG)
    if "@exampleBook2024" in introduction.read_text(encoding="utf-8"):
        fail("the starter manuscript must not contain the test-only citation")
    with introduction.open("a", encoding="utf-8") as source:
        source.write(
            "\n\n## Integration fixture\n\n"
            f"{INTRO_MARKER}\n\n"
            "This note cites the bibliography fixture [@exampleBook2024, 1-2].\n\n"
            f"![{FIGURE_ALT}](/resources/integration-fixture.png)\n"
        )
    with conclusion.open("a", encoding="utf-8") as source:
        source.write(
            "\n\n"
            "::: {.content-visible when-format=\"gfm\"}\n"
            f"{GFM_MARKER}\n"
            ":::\n\n"
            "::: {.content-hidden when-format=\"gfm\"}\n"
            f"{PAGINATED_MARKER}\n"
            ":::\n\n"
            f"{CONCLUSION_MARKER}\n"
        )


def inspect(project: Path, profile: str | None = None) -> dict:
    command = [QUARTO, "inspect"]
    if profile:
        command.extend(["--profile", profile])
    payload = json.loads(run(*command, cwd=project))
    config = payload.get("config")
    if not isinstance(config, dict):
        fail("quarto inspect did not return an effective project configuration")
    return config


def option_values(value: object) -> set[str]:
    if isinstance(value, str):
        return {item.strip() for item in value.split(",") if item.strip()}
    if isinstance(value, list):
        return {
            option
            for item in value
            if isinstance(item, str)
            for option in option_values(item)
        }
    return set()


def assert_configuration(project: Path) -> dict:
    ordinary = inspect(project)
    binding = inspect(project, "binding")

    formats = ordinary.get("format", {})
    if not isinstance(formats, dict) or set(formats) != {"pdf", "docx"}:
        fail("the project must expose only native PDF and DOCX formats")
    ordinary_pdf = formats.get("pdf", {})
    binding_pdf = binding.get("format", {}).get("pdf", {})
    if not isinstance(ordinary_pdf, dict) or not isinstance(binding_pdf, dict):
        fail("both ordinary and binding profiles must configure PDF output")
    if "documentclass" in ordinary_pdf or "documentclass" in binding_pdf:
        fail("PDF profiles must rely on Quarto's default document class")

    ordinary_options = option_values(ordinary_pdf.get("classoption"))
    binding_options = option_values(binding_pdf.get("classoption"))
    if ordinary_options != {"twoside=semi", "openright"}:
        fail(
            "ordinary PDF must use KOMA's default symmetric margins with recto starts"
        )
    if binding_options != {"twoside", "openright"}:
        fail("binding PDF must use KOMA's default mirrored margins with recto starts")
    if "geometry" in ordinary_pdf or "geometry" in binding_pdf:
        fail("PDF profiles must leave margin dimensions to KOMA")

    if ordinary.get("book", {}).get("output-file") != "longform-document":
        fail("ordinary output filename changed unexpectedly")
    if binding.get("book", {}).get("output-file") != "longform-document-binding":
        fail("binding profile does not declare its distinct output filename")
    return ordinary


def require_file(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        fail(f"missing or empty build artifact: {path}")


def assert_order(text: str, values: list[str], label: str) -> None:
    offset = -1
    for value in values:
        found = text.find(value, offset + 1)
        if found < 0:
            fail(f"{label} is missing ordered content: {value!r}")
        offset = found


def normalize_pdf_text(text: str) -> str:
    """Discard pagination-only text while retaining manuscript content."""
    kept: list[str] = []
    for raw_line in unicodedata.normalize("NFKC", text).splitlines():
        # PDF text extraction represents a TOC leader as dots or a wide run of
        # spaces. Binding changes those page numbers without changing prose.
        leader = re.search(r"(?:\s+\.){3}", raw_line)
        line = raw_line[:leader.start()] if leader else raw_line
        line = re.sub(r"\s{3,}\d+\s*$", "", line).strip()
        if re.fullmatch(r"(?:\d+|[ivxlcdm]+)", line, re.IGNORECASE):
            continue
        kept.append(line)
    return re.sub(r"\s+", " ", " ".join(kept)).strip()


def assert_pdf(path: Path) -> tuple[str, int]:
    require_file(path)
    if not path.read_bytes().startswith(b"%PDF-"):
        fail(f"invalid PDF header: {path.name}")
    information = run("pdfinfo", str(path), cwd=path.parent)
    pages = re.search(r"^Pages:\s+(\d+)$", information, re.MULTILINE)
    if pages is None or int(pages.group(1)) < 1:
        fail(f"PDF has no pages: {path.name}")
    page_count = int(pages.group(1))
    page_size = re.search(r"^Page size:\s+(.+)$", information, re.MULTILINE)
    if page_size is None or "A4" not in page_size.group(1):
        fail(f"PDF is not A4: {path.name}")

    text = run("pdftotext", "-layout", str(path), "-", cwd=path.parent)
    assert_order(
        text,
        [INTRO_MARKER, PAGINATED_MARKER, CONCLUSION_MARKER, "The Example Book"],
        path.name,
    )
    if GFM_MARKER in text:
        fail(f"{path.name} retained GFM-only conditional content")
    return normalize_pdf_text(text), page_count


def pdf_marker_position(path: Path, marker: str) -> tuple[int, float]:
    """Return the physical page and left edge of a unique rendered marker."""
    payload = run("pdftotext", "-bbox-layout", str(path), "-", cwd=path.parent)
    root = ET.fromstring(payload)
    needle = marker.split()
    matches: list[tuple[int, float]] = []
    pages = [node for node in root.iter() if node.tag.endswith("}page")]
    for page_number, page in enumerate(pages, start=1):
        words = [node for node in page.iter() if node.tag.endswith("}word")]
        values = [unicodedata.normalize("NFKC", node.text or "") for node in words]
        for index in range(len(values) - len(needle) + 1):
            if values[index:index + len(needle)] == needle:
                matches.append((page_number, float(words[index].attrib["xMin"])))
    if len(matches) != 1:
        fail(
            f"expected one positioned marker in {path.name}, found "
            f"{len(matches)}: {marker!r}"
        )
    return matches[0]


def pdf_heading_pages(path: Path, headings: tuple[str, ...]) -> dict[str, int]:
    """Locate rendered chapter headings by physical PDF page."""
    payload = run("pdftotext", "-layout", str(path), "-", cwd=path.parent)
    pages = payload.split("\f")
    result: dict[str, int] = {}
    for heading in headings:
        matches = [
            page_number
            for page_number, page in enumerate(pages, start=1)
            if any(line.strip() == heading for line in page.splitlines())
        ]
        if not matches:
            fail(f"could not locate PDF chapter heading in {path.name}: {heading!r}")
        result[heading] = matches[-1]
    return result


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
        "word/footnotes.xml",
    }
    with ZipFile(path) as archive:
        if corrupt := archive.testzip():
            fail(f"DOCX contains a corrupt member: {corrupt}")
        if missing := required - set(archive.namelist()):
            fail(f"DOCX is missing package members: {', '.join(sorted(missing))}")
        document = ET.fromstring(archive.read("word/document.xml"))
        styles = ET.fromstring(archive.read("word/styles.xml"))
        footnotes = ET.fromstring(archive.read("word/footnotes.xml"))
        media = {
            name for name in archive.namelist() if name.startswith("word/media/")
        }

    document_text = xml_text(document)
    assert_order(
        document_text,
        [
            title,
            "Introduction",
            INTRO_MARKER,
            "Conclusion",
            CONCLUSION_MARKER,
            "Bibliography",
            "The Example Book",
        ],
        "DOCX",
    )
    if GFM_MARKER in document_text or PAGINATED_MARKER not in document_text:
        fail("DOCX did not resolve format-conditional content correctly")

    style_ids = attribute_values(styles, "style", "styleId")
    used_styles = attribute_values(document, "pStyle", "val")
    for style in ("TOCHeading", "Bibliography"):
        if style not in style_ids:
            fail(f"DOCX reference style is missing: {style}")
        if style not in used_styles:
            fail(f"DOCX reference style is not applied: {style}")

    footnote_text = xml_text(footnotes)
    for value in ("The Example Book", "Example Press", "1–2"):
        if value not in footnote_text:
            fail(f"DOCX citation footnote is missing: {value!r}")
    if not media:
        fail("DOCX did not embed the manuscript figure")


def assert_gfm(path: Path) -> None:
    require_file(path)
    text = path.read_text(encoding="utf-8")
    assert_order(
        text,
        [
            "# Introduction",
            INTRO_MARKER,
            "# Conclusion",
            GFM_MARKER,
            CONCLUSION_MARKER,
            "# Bibliography",
            "The Example Book",
        ],
        "GFM",
    )
    if PAGINATED_MARKER in text:
        fail("GFM retained content intended only for paginated formats")
    for expected in ("[^", "Alex Example", "The Example Book", "Example Press"):
        if expected not in text:
            fail(f"GFM is missing rendered citation content: {expected!r}")
    for leaked in (
        "@exampleBook2024",
        "content-visible",
        "content-hidden",
        "when-format",
        "{{<",
        ":::",
        "\\chapter",
        "\\newpage",
    ):
        if leaked in text:
            fail(f"GFM contains unprocessed source markup: {leaked!r}")

    alt_pattern = r"\s+".join(map(re.escape, FIGURE_ALT.split()))
    markdown_image = re.search(rf"!\[{alt_pattern}\]\(([^)]+)\)", text)
    target = (
        markdown_image.group(1).split(maxsplit=1)[0].strip("<>")
        if markdown_image is not None
        else None
    )
    if target is None:
        for tag in re.findall(r"<img\b[^>]*>", text):
            if f'alt="{FIGURE_ALT}"' not in tag:
                continue
            source = re.search(r'\bsrc="([^"]+)"', tag)
            if source is not None:
                target = source.group(1)
                break
    if target is None:
        related = "\n".join(
            line for line in text.splitlines()
            if "Integration fixture" in line or "integration-fixture" in line
        )
        fail(f"GFM is missing the manuscript figure\n{related}")
    extracted = (path.parent / target).resolve()
    media_root = (path.parent / f"{path.stem}_files").resolve()
    if not extracted.is_relative_to(media_root) or not extracted.is_file():
        fail(f"GFM figure was not extracted beside the Markdown: {target}")
    if extracted.read_bytes() != ONE_PIXEL_PNG:
        fail("GFM extracted the wrong media bytes")


def assert_no_intermediates(project: Path, build: Path) -> None:
    tex_files = sorted(build.rglob("*.tex"))
    if tex_files:
        fail("build retained LaTeX intermediates: " + ", ".join(map(str, tex_files)))
    temporary = [
        path
        for path in project.iterdir()
        if path.name.startswith(
            (
                ".longform-gfm",
                ".longform-media",
                "longform-gfm",
                "_quarto-longform-gfm",
            )
        )
    ]
    if temporary:
        fail("build retained temporary GFM sources: " + ", ".join(map(str, temporary)))
    if (project / "index.tex").exists():
        fail("build retained Quarto's root LaTeX intermediate: index.tex")


def resolve_from(base: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def assert_zettlr(project: Path, config: dict) -> None:
    run(
        QUARTO,
        "run",
        "scripts/longform.ts",
        "zettlr",
        cwd=project,
        capture=False,
    )
    generated = project / "document/.ztr-directory"
    require_file(generated)
    if generated.is_symlink():
        fail("document/.ztr-directory must be a generated regular file")
    payload = json.loads(generated.read_text(encoding="utf-8"))
    zettlr_project = payload.get("project", {})

    expected_files: list[Path] = []
    for chapter in config.get("book", {}).get("chapters", []):
        if chapter == "index.md":
            expected_files.append((project / "document/front-matter.md").resolve())
        else:
            expected_files.append((project / chapter).resolve())
    actual_files = [
        resolve_from(generated.parent, value)
        for value in zettlr_project.get("files", [])
        if isinstance(value, str)
    ]
    if actual_files != expected_files:
        fail("Zettlr file order does not match the effective Quarto chapter order")
    csl_style = zettlr_project.get("cslStyle")
    if not isinstance(csl_style, str) or resolve_from(generated.parent, csl_style) != STYLE:
        fail("Zettlr configuration does not use the effective local CSL path")


def assert_ignored_generated_files() -> None:
    for relative in ("_quarto.yml.local", "document/.ztr-directory"):
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "--quiet", relative],
            cwd=ROOT,
            check=False,
        )
        if result.returncode != 0:
            fail(f"generated local file is not ignored: {relative}")


def test_build() -> None:
    require_tools()
    assert_ignored_generated_files()
    with tempfile.TemporaryDirectory(prefix="longform-kit-test-") as test_area:
        project = Path(test_area) / "project with spaces"
        copy_project(project)
        write_local_configuration(project)
        add_test_manuscript_content(project)
        config = assert_configuration(project)
        progress("configuration verified; rendering four outputs")

        run(
            QUARTO,
            "run",
            "scripts/longform.ts",
            "build",
            cwd=project,
            capture=False,
        )
        progress("build command completed; inspecting artifacts")
        build = project / config.get("project", {}).get("output-dir", "build")
        ordinary_pdf = build / "longform-document.pdf"
        binding_pdf = build / "longform-document-binding.pdf"
        docx = build / "longform-document.docx"
        gfm = build / "longform-document.md"
        for artifact in (ordinary_pdf, binding_pdf, docx, gfm):
            require_file(artifact)

        ordinary_text, ordinary_pages = assert_pdf(ordinary_pdf)
        binding_text, binding_pages = assert_pdf(binding_pdf)
        if ordinary_text != binding_text:
            difference = "\n".join(
                list(
                    difflib.unified_diff(
                        ordinary_text.split(),
                        binding_text.split(),
                        fromfile="ordinary.pdf",
                        tofile="binding.pdf",
                        lineterm="",
                    )
                )[:80]
            )
            fail(
                "ordinary and binding PDFs contain different normalized manuscript text"
                f"\n{difference}"
            )
        if ordinary_pdf.read_bytes() == binding_pdf.read_bytes():
            fail("ordinary and binding PDFs are byte-identical; profile was not applied")
        if binding_pages != ordinary_pages:
            fail(
                "ordinary and binding PDFs must retain the same recto padding; "
                f"found {ordinary_pages} and {binding_pages} pages"
            )
        headings = ("Preface", "Introduction", "Conclusion", "Bibliography")
        ordinary_heading_pages = pdf_heading_pages(ordinary_pdf, headings)
        binding_heading_pages = pdf_heading_pages(binding_pdf, headings)
        if ordinary_heading_pages != binding_heading_pages:
            fail(
                "ordinary and binding PDFs disagree on recto chapter pages: "
                f"{ordinary_heading_pages} / {binding_heading_pages}"
            )
        for heading, page in ordinary_heading_pages.items():
            if page % 2 == 0:
                fail(f"PDF chapter did not begin on a recto page: {heading!r}")
        for marker in (INTRO_MARKER, CONCLUSION_MARKER):
            ordinary_page, ordinary_x = pdf_marker_position(ordinary_pdf, marker)
            binding_page, binding_x = pdf_marker_position(binding_pdf, marker)
            if ordinary_page != binding_page:
                fail(f"PDF profiles disagree on the chapter page: {marker!r}")
            if ordinary_x - binding_x < 10:
                fail(
                    "binding PDF did not apply KOMA's default mirrored margins; "
                    f"recto offset was only {ordinary_x - binding_x:.2f}pt"
                )
        progress("ordinary and binding PDFs verified")

        title = config.get("book", {}).get("title", "A Longform Document")
        assert_docx(docx, title)
        progress("DOCX verified")
        assert_gfm(gfm)
        progress("combined GFM verified")
        assert_no_intermediates(project, build)
        assert_zettlr(project, config)
        progress("Zettlr configuration verified")


if __name__ == "__main__":
    try:
        test_build()
    except (AssertionError, OSError, ValueError, BadZipFile) as error:
        print(f"test_build: {error}", file=sys.stderr)
        raise SystemExit(1)
    print("test_build: all Longform Kit outputs passed structural verification")
