#!/usr/bin/env python3
"""Verify the optional-feature catalogue and documentation contract."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from xml.etree import ElementTree as ET
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[2]
FEATURES = ROOT / "publishing/features"
REFERENCE = ROOT / "publishing/docx/reference.docx"
TYPOGRAPHY_REFERENCE = FEATURES / "docx-typography/reference.docx"
QUARTO = os.environ.get("QUARTO", "quarto")
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = lambda name: f"{{{W_NS}}}{name}"
REQUIRED_PHRASES = (
    "Status: optional and disabled by default",
    "Purpose and affected outputs",
    "Requirements and external dependencies",
    "Complete `_quarto-custom.yml` activation snippet",
    "Metadata or Markdown interface",
    "Compatibility and ordering",
    "Disable or uninstall",
    "Failure behaviour",
    "Verification command",
    "Ownership and licence",
)


def fail(message: str) -> None:
    raise AssertionError(message)


def run(
    command: list[str],
    *,
    cwd: Path,
    environment: dict[str, str] | None = None,
    success: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if (result.returncode == 0) != success:
        expectation = "succeed" if success else "fail"
        fail(
            f"command should {expectation}: {' '.join(command)}\n{result.stdout}"
        )
    return result


def paragraph_style(paragraph: ET.Element) -> str | None:
    node = paragraph.find(f"./{W('pPr')}/{W('pStyle')}")
    return None if node is None else node.get(W("val"))


def document_styles(path: Path) -> list[str]:
    with ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    return [
        style
        for paragraph in root.findall(f".//{W('p')}")
        if (style := paragraph_style(paragraph)) is not None
    ]


def document_text(path: Path) -> str:
    with ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    return "".join(node.text or "" for node in root.iter(W("t")))


def defined_styles(path: Path) -> set[str]:
    with ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/styles.xml"))
    return {
        item.get(W("styleId"), "")
        for item in root.findall(W("style"))
    }


def embedded_fonts(path: Path) -> list[str]:
    with ZipFile(path) as archive:
        return [name for name in archive.namelist() if name.endswith(".odttf")]


def render_docx(
    directory: Path,
    markdown: str,
    *,
    filters: tuple[Path, ...] = (),
    reference: Path = REFERENCE,
    name: str = "fixture",
) -> Path:
    source = directory / f"{name}.md"
    output = directory / f"{name}.docx"
    source.write_text(markdown, encoding="utf-8")
    command = [
        QUARTO,
        "pandoc",
        str(source),
        "--standalone",
        "--toc",
        "--reference-doc",
        str(reference),
    ]
    for filter_path in filters:
        command.extend(("--lua-filter", str(filter_path)))
    command.extend(("--output", str(output)))
    run(command, cwd=directory)
    if not output.is_file() or output.stat().st_size == 0:
        fail("DOCX fixture was not rendered")
    return output


def process(
    script: Path,
    path: Path,
    environment: dict[str, str] | None = None,
) -> None:
    run(
        [sys.executable, str(script), str(path)],
        cwd=path.parent,
        environment=environment,
    )


ACADEMIC_MARKDOWN = """---
title: Fixture Title
subtitle: Fixture Subtitle
author: Alex Example
date: 1 January 2026
academic-title-page:
  student-number: "12345678"
  degree: Fixture degree
  supervisor: Dr A. Supervisor
  institute: Fixture University
---

# Chapter One

Body.
"""


EPIGRAPH_MARKDOWN = """---
title: Fixture Title
author: Alex Example
---

::: {.front-epigraph width=".60" blank-before="true" pagebreak-after="false"}
> Front quotation.

> Front source.
:::

# Chapter One

::: {.epigraph width=".75" separator="true" leading-break="true"}
> Body quotation.

> Body source.
:::

First paragraph.
"""


def typography_markdown(chapter_count: int, integrations: bool) -> str:
    metadata = """---
title: Variable Fixture
subtitle: Variable Subtitle
author: Alex Example
date: 1 January 2026
subject: Fixture subject
keywords: [fixture, variable]
"""
    if integrations:
        metadata += """academic-title-page:
  student-number: "12345678"
  degree: Fixture degree
  supervisor: Dr A. Supervisor
  institute: Fixture University
"""
    blocks = [metadata + "---\n"]
    if integrations:
        blocks.append(
            """::: {.front-epigraph width=".60" pagebreak-after="false"}
> Front quotation.

> Front source.
:::
"""
        )
    for index in range(1, chapter_count + 1):
        blocks.append(
            f"# Chapter {index}\n\nBody {index}.[^n{index}]\n\n"
            f"[^n{index}]: Note {index}.\n"
        )
    return "\n".join(blocks)


def test_contract() -> None:
    root_config = (ROOT / "_quarto.yml").read_text(encoding="utf-8")
    if "publishing/features/" in root_config:
        fail("root _quarto.yml references an optional feature")

    custom_lines = [
        line.strip()
        for line in (ROOT / "_quarto-custom.yml").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if custom_lines != ["{}"]:
        fail("the starter custom profile must remain an empty mapping")

    catalogue = (FEATURES / "README.md").read_text(encoding="utf-8")
    feature_directories = sorted(
        path
        for path in FEATURES.iterdir()
        if path.is_dir() and not path.name.startswith("_")
    )
    for directory in feature_directories:
        if f"`{directory.name}`" not in catalogue:
            fail(f"optional feature is missing from the catalogue: {directory.name}")
        readme = directory / "README.md"
        if not readme.is_file():
            fail(f"optional feature lacks README: {directory.name}")
        text = readme.read_text(encoding="utf-8")
        for phrase in REQUIRED_PHRASES:
            if phrase not in text:
                fail(
                    f"{directory.name}/README.md lacks contract section: {phrase}"
                )

    for directory in sorted(
        path
        for path in FEATURES.iterdir()
        if path.is_dir() and path.name.startswith("_")
    ):
        readme = directory / "README.md"
        if not readme.is_file() or "not an activatable feature" not in (
            readme.read_text(encoding="utf-8")
        ):
            fail(f"{directory.name} does not document its internal-only status")


def test_academic_title_page() -> None:
    lua_filter = FEATURES / "academic-title-page/filter.lua"
    processor = FEATURES / "academic-title-page/docx.py"
    with tempfile.TemporaryDirectory(prefix="longform-academic-title-") as area:
        directory = Path(area)
        output = render_docx(directory, ACADEMIC_MARKDOWN, filters=(lua_filter,))
        process(processor, output)
        first = output.read_bytes()
        process(processor, output)
        if output.read_bytes() != first:
            fail("academic title DOCX processor is not idempotent")
        expected = [
            "Title", "Subtitle", "Author", "StudentNumber", "Degree",
            "Supervisor", "Date", "Institute",
        ]
        observed = [style for style in document_styles(output) if style in expected]
        if observed != expected:
            fail(f"academic title fields are misordered: {observed}")
        definitions = defined_styles(output)
        for style in ("StudentNumber", "Degree", "Supervisor", "Institute"):
            if style not in definitions:
                fail(f"academic title processor did not supply {style}")

        custom_labels = ACADEMIC_MARKDOWN.replace(
            "  institute: Fixture University",
            "  institute: Fixture University\n"
            "  labels:\n"
            "    student-number: Candidate number\n"
            "    supervisor: Advised by",
        )
        labelled = render_docx(
            directory, custom_labels, filters=(lua_filter,), name="custom-labels"
        )
        process(processor, labelled)
        text = document_text(labelled)
        if (
            "Candidate number: 12345678" not in text
            or "Advised by Dr A. Supervisor" not in text
        ):
            fail("academic title labels are not configurable")

        malformed = directory / "malformed-title.md"
        malformed.write_text(
            ACADEMIC_MARKDOWN.replace(
                "academic-title-page:\n  student-number: \"12345678\"\n"
                "  degree: Fixture degree\n  supervisor: Dr A. Supervisor\n"
                "  institute: Fixture University",
                "academic-title-page: enabled",
            ),
            encoding="utf-8",
        )
        run(
            [
                QUARTO, "pandoc", str(malformed), "--lua-filter",
                str(lua_filter), "-t", "native",
            ],
            cwd=directory,
            success=False,
        )


def test_epigraph() -> None:
    lua_filter = FEATURES / "epigraph/filter.lua"
    processor = FEATURES / "epigraph/docx.py"
    with tempfile.TemporaryDirectory(prefix="longform-epigraph-") as area:
        directory = Path(area)
        output = render_docx(directory, EPIGRAPH_MARKDOWN, filters=(lua_filter,))
        process(processor, output)
        first = output.read_bytes()
        process(processor, output)
        if output.read_bytes() != first:
            fail("epigraph DOCX processor is not idempotent")
        expected = {
            "FrontEpigraphText60", "FrontEpigraphSource60",
            "EpigraphText75", "EpigraphSource75Separator", "FirstParagraph",
        }
        styles = set(document_styles(output))
        if not expected.issubset(styles):
            fail(f"epigraph DOCX styles are incomplete: {sorted(styles)}")
        if not expected.issubset(defined_styles(output)):
            fail("epigraph processor did not supply its styles")

        latex = directory / "epigraph.tex"
        source = directory / "epigraph.md"
        source.write_text(EPIGRAPH_MARKDOWN, encoding="utf-8")
        run(
            [
                QUARTO, "pandoc", str(source), "--lua-filter",
                str(lua_filter), "-t", "latex", "-o", str(latex),
            ],
            cwd=directory,
        )
        rendered = latex.read_text(encoding="utf-8")
        if "\\epigraph{" not in rendered or "\\LongformEpigraphSeparator" not in rendered:
            fail("epigraph filter did not render its PDF interface")

        malformed = directory / "malformed-epigraph.md"
        malformed.write_text(
            "::: {.epigraph}\n> Only one quote.\n:::\n", encoding="utf-8"
        )
        run(
            [
                QUARTO, "pandoc", str(malformed), "--lua-filter",
                str(lua_filter), "-t", "latex",
            ],
            cwd=directory,
            success=False,
        )


def test_combined() -> None:
    title_filter = FEATURES / "academic-title-page/filter.lua"
    epigraph_filter = FEATURES / "epigraph/filter.lua"
    markdown = ACADEMIC_MARKDOWN.replace(
        "# Chapter One",
        "::: {.front-epigraph width=\".60\" pagebreak-after=\"false\"}\n"
        "> Combined quotation.\n\n> Combined source.\n:::\n\n# Chapter One",
    )
    with tempfile.TemporaryDirectory(prefix="longform-combined-features-") as area:
        directory = Path(area)
        output = render_docx(
            directory,
            markdown,
            filters=(title_filter, epigraph_filter),
        )
        process(FEATURES / "academic-title-page/docx.py", output)
        process(FEATURES / "epigraph/docx.py", output)
        styles = document_styles(output)
        if styles.index("Institute") >= styles.index("FrontEpigraphText60"):
            fail("combined title and epigraph processors ran in the wrong order")


def run_typography_pipeline(
    directory: Path,
    chapter_count: int,
    integrations: bool,
) -> Path:
    filters: tuple[Path, ...] = ()
    if integrations:
        filters = (
            FEATURES / "academic-title-page/filter.lua",
            FEATURES / "epigraph/filter.lua",
        )
    output = render_docx(
        directory,
        typography_markdown(chapter_count, integrations),
        filters=filters,
        reference=TYPOGRAPHY_REFERENCE,
        name=f"typography-{chapter_count}-{integrations}",
    )
    if integrations:
        process(FEATURES / "academic-title-page/docx.py", output)
        process(FEATURES / "epigraph/docx.py", output)

    environment = os.environ.copy()
    environment["LONGFORM_EMBED_DOCX_FONTS"] = "0"
    environment["LONGFORM_EB_GARAMOND_DIR"] = (
        "relative-path-must-not-be-read"
    )
    process(FEATURES / "docx-typography/prepare.py", output, environment)
    prepared = output.read_bytes()
    process(FEATURES / "docx-typography/prepare.py", output, environment)
    if output.read_bytes() != prepared:
        fail("DOCX typography preparation is not idempotent")
    process(FEATURES / "docx-typography/stabilize.py", output, environment)
    stabilized = output.read_bytes()
    process(FEATURES / "docx-typography/stabilize.py", output, environment)
    if output.read_bytes() != stabilized:
        fail("DOCX typography stabilization is not idempotent")
    if embedded_fonts(output):
        fail("DOCX typography embedded fonts without explicit opt-in")
    return output


def test_docx_typography() -> None:
    build_reference = FEATURES / "docx-typography/build_reference.py"
    run([sys.executable, str(build_reference), "--check"], cwd=ROOT)
    with tempfile.TemporaryDirectory(
        prefix="longform-docx-typography-"
    ) as area:
        directory = Path(area)
        output: Path | None = None
        for count in (1, 4):
            output = run_typography_pipeline(directory, count, count == 4)
            styles = document_styles(output)
            if styles.count("Heading1") != count:
                fail("DOCX typography did not preserve variable H1 counts")

        if output is None:
            fail("DOCX typography fixture was not rendered")
        font_environment = os.environ.copy()
        font_environment["LONGFORM_EMBED_DOCX_FONTS"] = "1"
        embedded = directory / "embedded.docx"
        shutil.copy2(output, embedded)
        process(
            FEATURES / "docx-typography/prepare.py",
            embedded,
            font_environment,
        )
        if len(embedded_fonts(embedded)) != 6:
            fail("font embedding opt-in did not add all six checked faces")

        missing = directory / "missing-fonts.docx"
        shutil.copy2(output, missing)
        original = missing.read_bytes()
        missing_environment = font_environment.copy()
        missing_environment["LONGFORM_EB_GARAMOND_DIR"] = str(
            directory / "missing"
        )
        result = run(
            [
                sys.executable,
                str(FEATURES / "docx-typography/prepare.py"),
                str(missing),
            ],
            cwd=directory,
            environment=missing_environment,
            success=False,
        )
        if (
            "font directory is missing" not in result.stdout
            or missing.read_bytes() != original
        ):
            fail("missing font failure was not fail-closed and atomic")

        wrong_dir = directory / "wrong-fonts"
        wrong_dir.mkdir()
        for filename in (
            "EBGaramond-Regular.otf",
            "EBGaramond-Italic.otf",
            "EBGaramond-Bold.otf",
            "EBGaramond-BoldItalic.otf",
            "EBGaramond-SemiBold.otf",
            "EBGaramond-SemiBoldItalic.otf",
        ):
            (wrong_dir / filename).write_bytes(b"not the checked font")
        wrong = directory / "wrong-checksum.docx"
        shutil.copy2(output, wrong)
        wrong_original = wrong.read_bytes()
        wrong_environment = font_environment.copy()
        wrong_environment["LONGFORM_EB_GARAMOND_DIR"] = str(wrong_dir)
        result = run(
            [
                sys.executable,
                str(FEATURES / "docx-typography/prepare.py"),
                str(wrong),
            ],
            cwd=directory,
            environment=wrong_environment,
            success=False,
        )
        if (
            "unexpected checksum" not in result.stdout
            or wrong.read_bytes() != wrong_original
        ):
            fail("font checksum failure was not fail-closed and atomic")


def test_failure_behaviour() -> None:
    scripts = (
        FEATURES / "academic-title-page/docx.py",
        FEATURES / "epigraph/docx.py",
        FEATURES / "docx-typography/prepare.py",
        FEATURES / "docx-typography/stabilize.py",
    )
    environment = os.environ.copy()
    environment.pop("QUARTO_PROJECT_OUTPUT_FILES", None)
    for script in scripts:
        run([sys.executable, str(script)], cwd=ROOT, environment=environment)
    with tempfile.TemporaryDirectory(prefix="longform-corrupt-docx-") as area:
        path = Path(area) / "corrupt.docx"
        path.write_bytes(b"not a zip package")
        original = path.read_bytes()
        for script in scripts:
            result = run(
                [sys.executable, str(script), str(path)],
                cwd=path.parent,
                success=False,
            )
            if "cannot read DOCX package" not in result.stdout:
                fail(f"{script.name} did not diagnose a corrupt package")
            if path.read_bytes() != original:
                fail(f"{script.name} damaged a corrupt source package")


TESTS = {
    "contract": test_contract,
    "academic-title-page": test_academic_title_page,
    "epigraph": test_epigraph,
    "combined": test_combined,
    "docx-typography": test_docx_typography,
    "failure-behaviour": test_failure_behaviour,
}


def main() -> None:
    requested = sys.argv[1:] or list(TESTS)
    unknown = sorted(set(requested) - set(TESTS))
    if unknown:
        raise SystemExit("unknown optional-feature test: " + ", ".join(unknown))
    for name in requested:
        print(f"test_optional_features: {name}", flush=True)
        TESTS[name]()
    print("test_optional_features: all requested checks passed")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, OSError, RuntimeError, ValueError) as error:
        print(f"test_optional_features: {error}", file=sys.stderr)
        raise SystemExit(1)
