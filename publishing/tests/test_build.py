#!/usr/bin/env python3
"""Build and inspect every public Longform Kit output in a disposable copy."""

from __future__ import annotations

import base64
import difflib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import unicodedata
from urllib.parse import unquote
import xml.etree.ElementTree as ET
from zipfile import BadZipFile, ZipFile


ROOT = Path(__file__).resolve().parents[2]
QUARTO = os.environ.get("QUARTO", "quarto")
QPDF = os.environ.get("QPDF", "qpdf")
LIBRARY = (ROOT / "publishing/tests/fixtures/library.json").resolve()
STYLE = (ROOT / "publishing/tests/fixtures/longform-test-note.csl").resolve()
WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"

INTRO_MARKER = "Integration fixture: the first chapter is present."
CONCLUSION_MARKER = "Integration fixture: the final chapter is present."
FRONT_MARKER = "Fixture: headingless front matter is present."
GFM_MARKER = "Integration fixture: this sentence belongs only in GFM."
PROFILE_MARKER = "Integration fixture: the active profile reached GFM."
PAGINATED_MARKER = (
    "Integration fixture: this sentence belongs only in paginated output."
)
FIGURE_ALT = "Integration fixture figure"
GLYPH_MARKER = "-> => != <= >= :: 0123456789"
SECTION_HEADING = "Fixture Section Omitted From Contents"
ODD_AREA_LEFT = "FixtureOddAreaLeft"
ODD_AREA_RIGHT = "FixtureOddAreaRight"
EVEN_AREA_LEFT = "FixtureEvenAreaLeft"
EVEN_AREA_RIGHT = "FixtureEvenAreaRight"
BOTTOM_AREA_LEFT = "FixtureBottomAreaLeft"
BOTTOM_AREA_RIGHT = "FixtureBottomAreaRight"
BASELINE_FIRST = "FixtureBaselineAB"
BASELINE_SECOND = "FixtureBaselineBA"
FOOTNOTE_FIRST = "FixtureFootnoteAB"
FOOTNOTE_SECOND = "FixtureFootnoteBA"
TEST_OUTPUT = "Longform Kit integration fixture"
FIXTURE_TITLE = "Longform Kit & Integration"
FIXTURE_SUBTITLE = "*A Fixture Subtitle*"
FIXTURE_SUBJECT = "Metadata {braces}, 100% & under_score #1"
PDF_POINTS_PER_MM = 72 / 25.4
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
    env: dict[str, str] | None = None,
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
            env=env,
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
    for command in (
        QUARTO,
        "git",
        "pdfjam",
        QPDF,
        "lualatex",
        "pdffonts",
        "pdfinfo",
        "pdftotext",
    ):
        if shutil.which(command) is None:
            fail(f"missing required command: {command}")
    for path in (LIBRARY, STYLE):
        if not path.is_file():
            fail(f"missing committed test fixture: {path.relative_to(ROOT)}")


def copy_project(destination: Path, source: Path = ROOT) -> None:
    """Copy allowed tracked files from their current worktree versions."""

    source = source.resolve()
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=source,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        output = result.stderr.decode(errors="replace")
        fail(f"could not list tracked project files:\n{output}")

    destination.mkdir(parents=True)
    excluded_roots = {"archive", "materials", "resources", "style"}
    manuscript_metadata = Path("writing/manuscript/metadata.yml")
    for encoded in result.stdout.split(b"\0"):
        if not encoded:
            continue
        relative = Path(os.fsdecode(encoded))
        if relative.parts[0] in excluded_roots:
            continue
        if relative.parts[0] == "writing" and relative != manuscript_metadata:
            continue

        # Metadata plus the tracked custom profile and publishing/features are
        # intentionally retained to validate downstream profile compatibility.
        source_path = source / relative
        try:
            mode = source_path.lstat().st_mode
        except FileNotFoundError:
            # A tracked path deleted in the worktree has no current version.
            continue
        destination_path = destination / relative
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        if stat.S_ISLNK(mode):
            destination_path.symlink_to(os.readlink(source_path))
        elif stat.S_ISREG(mode):
            shutil.copy2(source_path, destination_path, follow_symlinks=False)
        else:
            fail(f"unsupported tracked project path: {relative}")


def assert_copy_project_boundaries() -> None:
    """Keep local and author material out while preserving extension inputs."""
    with tempfile.TemporaryDirectory(prefix="longform-copy-boundaries-") as area:
        source = Path(area) / "source"
        destination = Path(area) / "destination"
        source.mkdir()
        run("git", "init", "--quiet", cwd=source)
        preserved = {
            Path(".gitignore"): "/ignored-local/\n",
            Path("_quarto-custom.yml"): "profile: custom\n",
            Path("publishing/features/example/filter.lua"): "return {}\n",
            Path("writing/manuscript/metadata.yml"): "title: Fixture\n",
        }
        excluded = (
            Path("archive/submissions/frozen.pdf"),
            Path("resources/figure.png"),
            Path("materials/source.png"),
            Path("style/Editorial Style Guide.md"),
            Path("writing/drafts/draft.md"),
            Path("writing/notes/note.md"),
            Path("writing/planning/plan.md"),
            Path("writing/correspondence/email.md"),
            Path("writing/manuscript/chapters.yml"),
            Path("writing/manuscript/front-matter.md"),
            Path("writing/manuscript/bibliography.md"),
            Path("writing/manuscript/chapters/chapter.md"),
        )
        for relative, content in preserved.items():
            path = source / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        for relative in excluded:
            path = source / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("downstream author fixture\n", encoding="utf-8")

        tracked_link = source / "publishing/features/example/tracked-filter.lua"
        tracked_link.symlink_to("filter.lua")
        run("git", "add", "--all", cwd=source)

        current_profile = "profile: current-worktree\n"
        (source / "_quarto-custom.yml").write_text(
            current_profile,
            encoding="utf-8",
        )
        preserved[Path("_quarto-custom.yml")] = current_profile

        ignored_payload = "ignored payload must not be copied"
        ignored_file = source / "ignored-local/sentinel.txt"
        ignored_file.parent.mkdir()
        ignored_file.write_text(ignored_payload, encoding="utf-8")
        untracked_payload = "untracked payload must not be copied"
        untracked_file = source / "arbitrary-local/sentinel.txt"
        untracked_file.parent.mkdir()
        untracked_file.write_text(untracked_payload, encoding="utf-8")
        untracked_link = source / "untracked-sentinel-link"
        untracked_link.symlink_to(ignored_file)

        copy_project(destination, source)

        for relative, expected in preserved.items():
            path = destination / relative
            require_file(path)
            if path.read_text(encoding="utf-8") != expected:
                fail(f"disposable copy changed preserved input: {relative}")
        leaked = [
            str(relative)
            for relative in excluded
            if (destination / relative).exists()
        ]
        if leaked:
            fail(
                "disposable copy retained downstream author material: "
                f"{', '.join(leaked)}"
            )
        copied_link = destination / tracked_link.relative_to(source)
        if not copied_link.is_symlink() or os.readlink(copied_link) != "filter.lua":
            fail("disposable copy did not preserve a tracked symlink")

        local_paths = (
            ignored_file.parent.relative_to(source),
            untracked_file.parent.relative_to(source),
            untracked_link.relative_to(source),
        )
        retained = [
            str(path)
            for path in local_paths
            if (destination / path).exists() or (destination / path).is_symlink()
        ]
        if retained:
            fail(f"disposable copy retained ignored or untracked paths: {retained}")
        copied_payload = b"\n".join(
            path.read_bytes()
            for path in destination.rglob("*")
            if not path.is_symlink() and path.is_file()
        )
        for payload in (ignored_payload, untracked_payload):
            if payload.encode() in copied_payload:
                fail("disposable copy retained an ignored or untracked payload")


def write_local_configuration(project: Path) -> None:
    # JSON strings are valid YAML scalars and safely preserve spaces in paths.
    (project / "_quarto.yml.local").write_text(
        f"bibliography: {json.dumps(str(LIBRARY))}\n"
        f"csl: {json.dumps(str(STYLE))}\n",
        encoding="utf-8",
    )


def write_tool_shims(project: Path) -> tuple[dict[str, str], Path, Path]:
    """Exercise executable overrides and strict PDF validation offline."""
    directory = project / "tool shims"
    directory.mkdir()
    qpdf_marker = directory / "qpdf-invocations.txt"
    verapdf_marker = directory / "verapdf-invocations.txt"

    qpdf_path = shutil.which(QPDF)
    if qpdf_path is None:
        fail("missing required command: qpdf")
    qpdf_shim = directory / "qpdf override"
    qpdf_shim.write_text(
        "#!/bin/sh\n"
        f"printf '%s\\n' \"$*\" >> {shlex.quote(str(qpdf_marker))}\n"
        f"exec {shlex.quote(qpdf_path)} \"$@\"\n",
        encoding="utf-8",
    )
    qpdf_shim.chmod(0o755)

    verapdf_shim = directory / "verapdf override"
    verapdf_shim.write_text(
        "#!/bin/sh\n"
        f"printf '%s\\n' \"$*\" >> {shlex.quote(str(verapdf_marker))}\n"
        "printf '%s\\n' '<validationReport isCompliant=\"true\"/>'\n",
        encoding="utf-8",
    )
    verapdf_shim.chmod(0o755)
    environment = os.environ.copy()
    environment.update(
        {
            "LONGFORM_VALIDATE_PDF": "1",
            "QPDF": str(qpdf_shim),
            "QUARTO_VERAPDF": str(verapdf_shim),
        }
    )
    return environment, qpdf_marker, verapdf_marker


def incoming_real_verapdf() -> str | None:
    """Return the caller-supplied release validator, if validation is enabled."""
    if os.environ.get("LONGFORM_VALIDATE_PDF") != "1":
        return None
    verifier = os.environ.get("QUARTO_VERAPDF", "").strip()
    if not verifier:
        return None
    candidate = Path(verifier)
    if not candidate.is_absolute() and ("/" in verifier or "\\" in verifier):
        return str((ROOT / candidate).resolve())
    return verifier


def assert_default_custom_profile(project: Path) -> None:
    """Confirm the shipped empty custom profile is active and inert."""
    profile = (project / "_quarto-custom.yml").resolve()
    require_file(profile)
    payload = json.loads(run(QUARTO, "inspect", cwd=project))
    files = payload.get("files", {}).get("config", [])
    if isinstance(files, str):
        files = [files]
    active = {
        resolve_from(project, value)
        for value in files
        if isinstance(value, str)
    }
    if profile not in active:
        fail("root _quarto.yml must activate the committed custom profile")
    config = payload.get("config", {})
    if configuration_contains(config, "publishing/features/"):
        fail("an empty custom profile must not enable optional features")


def write_test_profile(project: Path) -> None:
    """Exercise default-profile merging and URL-safe output names."""
    path = project / "_quarto.yml"
    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        profile_line = lines.index("profile:")
    except ValueError:
        lines.extend(("", "profile:", "  default: integration"))
    else:
        for index in range(profile_line + 1, len(lines)):
            line = lines[index]
            if line and not line[0].isspace():
                lines.insert(profile_line + 1, "  default: integration")
                break
            if line.lstrip().startswith("default:"):
                lines[index] = "  default: integration"
                break
        else:
            lines.insert(profile_line + 1, "  default: integration")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (project / "_quarto-integration.yml").write_text(
        "book:\n"
        f'  output-file: "{TEST_OUTPUT}"\n',
        encoding="utf-8",
    )


def write_test_manuscript(project: Path) -> None:
    """Replace the configured manuscript with a self-contained test fixture."""
    manuscript = project / "writing/manuscript"
    chapters = manuscript / "chapters"
    introduction = chapters / "longform-test-introduction.md"
    conclusion = chapters / "longform-test-conclusion.md"
    figure = project / "materials/integration-fixture.png"
    chapters.mkdir(parents=True, exist_ok=True)
    figure.parent.mkdir(exist_ok=True)
    figure.write_bytes(ONE_PIXEL_PNG)
    (manuscript / "metadata.yml").write_text(
        "lang: en-GB\n"
        f"title-meta: {json.dumps(f'{FIXTURE_TITLE}: A Fixture Subtitle')}\n"
        f"subject: {json.dumps(FIXTURE_SUBJECT)}\n"
        "keywords:\n"
        "  - one & two\n"
        "  - 100% fixture\n"
        "book:\n"
        '  output-file: "Longform fixture"\n'
        f"  title: {json.dumps(FIXTURE_TITLE)}\n"
        f"  subtitle: {json.dumps(FIXTURE_SUBTITLE)}\n"
        '  author: "Alex Example"\n'
        '  date: "1 January 2026"\n'
        '  date-format: "D MMMM YYYY"\n',
        encoding="utf-8",
    )
    (manuscript / "chapters.yml").write_text(
        "book:\n"
        "  chapters:\n"
        "    - index.md\n"
        "    - writing/manuscript/chapters/longform-test-introduction.md\n"
        "    - writing/manuscript/chapters/longform-test-conclusion.md\n"
        "    - writing/manuscript/bibliography.md\n",
        encoding="utf-8",
    )
    (manuscript / "front-matter.md").write_text(
        f"> {FRONT_MARKER}\n\n"
        "{{< pagebreak >}}\n",
        encoding="utf-8",
    )
    introduction.write_text(
        "# Introduction\n\n"
        "```{=latex}\n"
        "\\pdfbookmark[0]{Fixture Introduction Bookmark}{fixture-introduction}\n"
        "\\pdfbookmark[1]{Fixture Nested Bookmark}{fixture-nested}\n"
        "```\n\n"
        f"## {SECTION_HEADING}\n\n"
        f"{INTRO_MARKER}\n\n"
        "```{=latex}\n"
        f"\\noindent\\makebox[\\textwidth][s]{{{ODD_AREA_LEFT}"
        f"\\hfill {ODD_AREA_RIGHT}}}\\par\n"
        f"\\noindent {BASELINE_FIRST}\\\\\n"
        f"{BASELINE_SECOND}\\par\n"
        "```\n\n"
        "{{< pagebreak >}}\n\n"
        "```{=latex}\n"
        f"\\noindent\\makebox[\\textwidth][s]{{{EVEN_AREA_LEFT}"
        f"\\hfill {EVEN_AREA_RIGHT}}}\\par\n"
        "\\vfill\n"
        f"\\noindent\\makebox[\\textwidth][s]{{{BOTTOM_AREA_LEFT}"
        f"\\hfill {BOTTOM_AREA_RIGHT}}}\\par\n"
        "```\n\n"
        "{{< pagebreak >}}\n\n"
        "```{=latex}\n"
        f"FixtureFootnoteCall\\footnote{{{FOOTNOTE_FIRST}\\newline\n"
        f"{FOOTNOTE_SECOND}}}\n"
        "```\n\n"
        "This note cites the bibliography fixture [@exampleBook2024, 1-2].\n\n"
        f"Operator extraction fixture: `{GLYPH_MARKER}`.\n\n"
        f"![{FIGURE_ALT}](/materials/integration-fixture.png)\n",
        encoding="utf-8",
    )
    conclusion.write_text(
        "# Conclusion {.unnumbered}\n\n"
        "```{=latex}\n"
        "\\pdfbookmark[0]{Fixture Conclusion Bookmark}{fixture-conclusion}\n"
        "```\n\n"
        "::: {.content-visible when-format=\"gfm\"}\n"
        f"{GFM_MARKER}\n"
        ":::\n\n"
        "::: {.content-visible when-profile=\"integration\"}\n"
        f"{PROFILE_MARKER}\n"
        ":::\n\n"
        "::: {.content-hidden when-format=\"gfm\"}\n"
        f"{PAGINATED_MARKER}\n"
        ":::\n\n"
        f"{CONCLUSION_MARKER}\n",
        encoding="utf-8",
    )
    (manuscript / "bibliography.md").write_text(
        "# Bibliography {.unnumbered}\n\n::: {#refs}\n:::\n",
        encoding="utf-8",
    )


def inspect(project: Path) -> dict:
    payload = json.loads(run(QUARTO, "inspect", cwd=project))
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


def configuration_contains(value: object, needle: str) -> bool:
    if isinstance(value, str):
        return needle in value
    if isinstance(value, list):
        return any(configuration_contains(item, needle) for item in value)
    if isinstance(value, dict):
        return any(configuration_contains(item, needle) for item in value.values())
    return False


def included_header_text(project: Path, pdf: dict) -> str:
    """Resolve effective inline and file-backed PDF header includes."""
    sources: list[str] = []
    includes = pdf.get("include-in-header", [])
    if not isinstance(includes, list):
        includes = [includes]
    for include in includes:
        if isinstance(include, str):
            path = resolve_from(project, include)
            if path.is_file():
                sources.append(path.read_text(encoding="utf-8"))
            else:
                sources.append(include)
        elif isinstance(include, dict):
            text = include.get("text")
            if isinstance(text, str):
                sources.append(text)
            file = include.get("file")
            if isinstance(file, str):
                path = resolve_from(project, file)
                require_file(path)
                sources.append(path.read_text(encoding="utf-8"))
    return "\n".join(sources)


def assert_configuration(project: Path) -> dict:
    root_configuration = (project / "_quarto.yml").read_text(encoding="utf-8")
    if "publishing/features/" in root_configuration:
        fail("root _quarto.yml must never reference optional features")
    config = inspect(project)
    formats = config.get("format", {})
    if not isinstance(formats, dict) or set(formats) != {"docx", "pdf"}:
        fail("the project must expose only the native PDF and DOCX formats")
    pdf = formats.get("pdf", {})
    if not isinstance(pdf, dict):
        fail("the project must configure PDF output")
    if "documentclass" in pdf:
        fail("the PDF must rely on Quarto's default document class")

    if config.get("toc") is not True:
        fail("the project must enable the table of contents")
    if config.get("toc-depth") != 1:
        fail("the project must list chapter headings only in the TOC")
    if config.get("number-sections") is not False:
        fail("the project must leave headings unnumbered")

    options = option_values(pdf.get("classoption"))
    if "openright" not in options or not any(
        option == "twoside" or option.startswith("twoside=")
        for option in options
    ):
        fail("PDF must use two-sided pagination with recto chapter starts")
    if "BCOR=0mm" not in options:
        fail("PDF must keep a neutral binding correction until specified")
    if "fontsize=15.25pt" not in options:
        fail("PDF must set KOMA's effective body size to 15.25pt")
    if any(option.startswith("DIV=") for option in options):
        fail("PDF must use the configured KOMA areaset instead of DIV")
    if "geometry" in pdf:
        fail("PDF must use KOMA typearea instead of geometry")
    expected_typography = {
        "pdf-engine": "lualatex",
        "linestretch": 1.055,
        "mainfont": "EB Garamond",
        "sansfont": "EB Garamond",
        "monofont": "EB Garamond",
    }
    for key, expected in expected_typography.items():
        if pdf.get(key) != expected:
            fail(f"PDF must set {key} to {expected!r}")
    if "fontsize" in pdf:
        fail(
            "the non-standard PDF body size must use KOMA's keyed class option, "
            "not Quarto's bare fontsize option"
        )
    for option in ("mainfontoptions", "sansfontoptions", "monofontoptions"):
        if option_values(pdf.get(option)) != {"Numbers=OldStyle"}:
            fail("PDF must use old-style EB Garamond figures")
    header_text = included_header_text(project, pdf)
    for required in (
        "\\usepackage[all]{nowidow}",
        "\\areaset[current]{140mm}{227mm}",
        "\\LongformSemibold",
        "\\AssignSocketPlug{build/column/outputbox}{footnotes-floats-legacy}",
    ):
        if required not in header_text:
            fail(f"core PDF typography is missing {required}")
    footnote_settings = (
        "\\fontsize{12.7pt}{16pt}\\selectfont",
        "\\deffootnote[1.5em]{1.5em}{1em}{\\thefootnotemark\\enskip}",
        "\\setfootnoterule[0pt]{0pt}",
    )
    for setting in footnote_settings:
        if setting not in header_text:
            fail("PDF must retain the configured footnote treatment")
    if "\\interfootnotelinepenalty" in header_text:
        fail("PDF must retain normal cross-page footnote splitting")
    if option_values(pdf.get("pdf-standard")) != {"a-4f"}:
        fail("core PDF must target PDF/A-4f")
    microtype = option_values(pdf.get("microtypeoptions"))
    for option in (
        "protrusion=true",
        "expansion=true",
        "tracking=false",
        "kerning=false",
        "spacing=false",
    ):
        if option not in microtype:
            fail(f"core PDF microtype options are missing {option}")
    partials = pdf.get("template-partials", [])
    if not configuration_contains(
        partials, "publishing/pdf/standards/document-metadata.latex"
    ):
        fail("core PDF/A compatibility partial is not registered")

    output = config.get("book", {}).get("output-file")
    if not isinstance(output, str) or not output.strip():
        fail("output filename must be a non-empty string")
    return config


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
    normalized = re.sub(r"\s+", " ", " ".join(kept)).strip()
    # A narrower binding type area may trigger discretionary hyphens at line
    # endings. Ignore those layout-only differences while still comparing the
    # complete normalized manuscript text.
    normalized = re.sub(r"(?<=\w)[-‐‑]\s+(?=\w)", "", normalized)
    return re.sub(r"(?<=\w)[-‐‑](?=\w)", "", normalized)


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
        [
            FRONT_MARKER,
            INTRO_MARKER,
            PAGINATED_MARKER,
            CONCLUSION_MARKER,
            "The Example Book",
        ],
        path.name,
    )
    if re.search(r"(?m)^[ \t\f]*Introduction[ \t]*$", text) is None:
        fail(f"{path.name} is missing the unnumbered Introduction heading")
    for heading in ("Introduction", SECTION_HEADING, "Conclusion", "Bibliography"):
        if re.search(
            rf"(?m)^[ \t\f]*\d+(?:\.\d+)*[.)]?[ \t]+"
            rf"{re.escape(heading)}(?:[ \t]|$)",
            text,
        ):
            fail(f"{path.name} rendered a numbered heading: {heading!r}")
    if text.count(SECTION_HEADING) != 1:
        fail(f"{path.name} included a section heading in the chapter-only TOC")
    if GFM_MARKER in text:
        fail(f"{path.name} retained GFM-only conditional content")
    if GLYPH_MARKER not in text:
        fail(f"{path.name} did not preserve inline-code glyph extraction")

    font_table = run("pdffonts", str(path), cwd=path.parent)
    font_rows = [line.split() for line in font_table.splitlines()[2:] if line.strip()]
    garamond_rows = [row for row in font_rows if "EBGaramond" in row[0]]
    if not garamond_rows:
        fail(f"{path.name} did not embed EB Garamond")
    if unexpected := sorted(
        {row[0] for row in font_rows if "EBGaramond" not in row[0]}
    ):
        fail(f"{path.name} embedded non-EB-Garamond text fonts: {unexpected}")
    if any(
        len(row) < 5 or row[-5:-2] != ["yes", "yes", "yes"]
        for row in garamond_rows
    ):
        fail(f"{path.name} must subset and embed EB Garamond with a Unicode map")
    return normalize_pdf_text(text), page_count


def pdf_marker_box(
    path: Path,
    marker: str,
) -> tuple[int, float, float, float, float]:
    """Return the page and bounding box of a unique rendered marker."""
    payload = run("pdftotext", "-bbox-layout", str(path), "-", cwd=path.parent)
    root = ET.fromstring(payload)
    needle = marker.split()
    matches: list[tuple[int, float, float, float, float]] = []
    pages = [node for node in root.iter() if node.tag.endswith("}page")]
    for page_number, page in enumerate(pages, start=1):
        words = [node for node in page.iter() if node.tag.endswith("}word")]
        values = [unicodedata.normalize("NFKC", node.text or "") for node in words]
        for index in range(len(values) - len(needle) + 1):
            if values[index:index + len(needle)] == needle:
                matches.append(
                    (
                        page_number,
                        float(words[index].attrib["xMin"]),
                        min(
                            float(word.attrib["yMin"])
                            for word in words[index:index + len(needle)]
                        ),
                        float(words[index + len(needle) - 1].attrib["xMax"]),
                        max(
                            float(word.attrib["yMax"])
                            for word in words[index:index + len(needle)]
                        ),
                    )
                )
    if len(matches) != 1:
        fail(
            f"expected one positioned marker in {path.name}, found "
            f"{len(matches)}: {marker!r}"
        )
    return matches[0]


def pdf_marker_bounds(path: Path, marker: str) -> tuple[int, float, float]:
    """Return the page and horizontal bounds of a unique rendered marker."""
    page, left, _, right, _ = pdf_marker_box(path, marker)
    return page, left, right


def pdf_page_size_mm(path: Path) -> tuple[float, float]:
    """Return the PDF page dimensions reported by Poppler, in millimetres."""
    information = run("pdfinfo", str(path), cwd=path.parent)
    match = re.search(
        r"^Page size:\s+([\d.]+) x ([\d.]+) pts",
        information,
        re.MULTILINE,
    )
    if match is None:
        fail(f"could not read the page size from {path.name}")
    width, height = map(float, match.groups())
    return width / PDF_POINTS_PER_MM, height / PDF_POINTS_PER_MM


def metadata_scalar(value: object) -> str:
    if isinstance(value, (str, int, float)):
        return str(value)
    if isinstance(value, list):
        return "; ".join(filter(None, map(metadata_scalar, value)))
    if isinstance(value, dict):
        return metadata_scalar(value.get("name", ""))
    return ""


def plain_metadata_text(value: object) -> str:
    result = metadata_scalar(value).strip()
    if len(result) >= 2 and (
        (result.startswith("*") and result.endswith("*"))
        or (result.startswith("_") and result.endswith("_"))
    ):
        result = result[1:-1]
    result = re.sub(r"`([^`]*)`", r"\1", result)
    result = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", result)
    result = re.sub(r"\*\*([^*]+)\*\*", r"\1", result)
    result = re.sub(r"__([^_]+)__", r"\1", result)
    result = re.sub(r"\*([^*]+)\*", r"\1", result)
    result = re.sub(r"_([^_\s](?:.*?[^_\s])?)_", r"\1", result)
    return re.sub(r"\s+", " ", result).strip()


def expected_publication_metadata(config: dict) -> dict[str, str]:
    book = config.get("book", {})
    if not isinstance(book, dict):
        book = {}
    title = plain_metadata_text(config.get("title-meta", ""))
    if not title:
        title = ": ".join(
            filter(
                None,
                (
                    plain_metadata_text(book.get("title", "")),
                    plain_metadata_text(book.get("subtitle", "")),
                ),
            )
        )
    raw_keywords = config.get("keywords", "")
    if isinstance(raw_keywords, list):
        keywords = ", ".join(
            filter(None, (plain_metadata_text(item) for item in raw_keywords))
        )
    else:
        keywords = plain_metadata_text(raw_keywords)
    return {
        "Title": title,
        "Author": plain_metadata_text(
            config.get("author-meta") or book.get("author", "")
        ),
        "Subject": plain_metadata_text(config.get("subject", "")),
        "Keywords": keywords,
        "Language": plain_metadata_text(config.get("lang", "")),
    }


def pdf_info_fields(path: Path) -> dict[str, str]:
    information = run("pdfinfo", str(path), cwd=path.parent)
    fields: dict[str, str] = {}
    for line in information.splitlines():
        key, separator, value = line.partition(":")
        if separator:
            fields[key.strip()] = value.strip()
    return fields


def qpdf_payload(path: Path, *keys: str) -> dict:
    arguments = [QPDF, "--json"]
    arguments.extend(f"--json-key={key}" for key in keys)
    arguments.append(str(path.resolve()))
    return json.loads(run(*arguments, cwd=path.parent))


def flatten_pdf_outlines(
    outlines: object,
    level: int = 0,
) -> list[tuple[str, int, int]]:
    flattened: list[tuple[str, int, int]] = []
    if not isinstance(outlines, list):
        return flattened
    for item in outlines:
        if not isinstance(item, dict):
            continue
        title = item.get("title")
        page = item.get("destpageposfrom1")
        if isinstance(title, str) and isinstance(page, int):
            flattened.append((title, page, level))
        flattened.extend(flatten_pdf_outlines(item.get("kids"), level + 1))
    return flattened


def pdf_catalog(path: Path) -> dict:
    payload = qpdf_payload(path, "qpdf")
    qpdf_objects = payload.get("qpdf", [])
    if not isinstance(qpdf_objects, list) or len(qpdf_objects) < 2:
        fail(f"qpdf did not return PDF objects for {path.name}")
    objects = qpdf_objects[1]
    if not isinstance(objects, dict):
        fail(f"qpdf returned invalid PDF objects for {path.name}")
    trailer = objects.get("trailer", {})
    if not isinstance(trailer, dict):
        fail(f"qpdf did not return a trailer for {path.name}")
    trailer_value = trailer.get("value", {})
    if not isinstance(trailer_value, dict):
        fail(f"qpdf returned an invalid trailer for {path.name}")
    root = trailer_value.get("/Root")
    catalog = objects.get(f"obj:{root}", {})
    if not isinstance(catalog, dict) or not isinstance(catalog.get("value"), dict):
        fail(f"qpdf did not return a catalog for {path.name}")
    return catalog["value"]


def assert_two_up_pdf(
    source: Path,
    two_up: Path,
    source_text: str,
    source_pages: int,
    title: str,
    config: dict,
) -> None:
    """Verify A4-landscape imposition with rectos in the right-hand slot."""
    two_up_text, two_up_pages = assert_pdf(two_up)
    expected_pages = (source_pages + 2) // 2
    if two_up_pages != expected_pages:
        fail(
            f"{two_up.name} has {two_up_pages} sheets; expected {expected_pages} "
            f"for {source_pages} source pages plus the leading blank slot"
        )
    source_words = sorted(source_text.split())
    two_up_words = sorted(two_up_text.split())
    if two_up_words != source_words:
        difference = "\n".join(
            list(
                difflib.unified_diff(
                    source_words,
                    two_up_words,
                    fromfile="document.pdf",
                    tofile="document-2up.pdf",
                    lineterm="",
                )
            )[:80]
        )
        fail(
            "source and two-up PDFs contain different normalized manuscript text"
            f"\n{difference}"
        )

    width_mm, height_mm = pdf_page_size_mm(two_up)
    if abs(width_mm - 297) > 0.2 or abs(height_mm - 210) > 0.2:
        fail(
            f"{two_up.name} is {width_mm:.1f} by {height_mm:.1f} mm; "
            "expected A4 landscape"
        )
    midpoint = width_mm * PDF_POINTS_PER_MM / 2
    for marker in (title, INTRO_MARKER, CONCLUSION_MARKER):
        source_page, _, _ = pdf_marker_bounds(source, marker)
        sheet, left, _ = pdf_marker_bounds(two_up, marker)
        expected_sheet = (source_page + 2) // 2
        if source_page % 2 != 1 or sheet != expected_sheet or left <= midpoint:
            fail(
                f"{two_up.name} did not place recto content in the right-hand "
                f"slot: {marker!r}"
            )

    source_page, _, _ = pdf_marker_bounds(source, EVEN_AREA_LEFT)
    sheet, _, right = pdf_marker_bounds(two_up, EVEN_AREA_LEFT)
    expected_sheet = (source_page + 2) // 2
    if source_page % 2 != 0 or sheet != expected_sheet or right >= midpoint:
        fail(
            f"{two_up.name} did not place verso content in the left-hand slot"
        )

    source_outlines = flatten_pdf_outlines(
        qpdf_payload(source, "outlines").get("outlines")
    )
    if not source_outlines:
        fail(f"{source.name} did not expose any bookmarks to remap")
    two_up_outlines = flatten_pdf_outlines(
        qpdf_payload(two_up, "outlines").get("outlines")
    )
    expected_outlines = [
        (outline_title, (page + 2) // 2, level)
        for outline_title, page, level in source_outlines
    ]
    if two_up_outlines != expected_outlines:
        fail(
            f"{two_up.name} did not remap source bookmarks to imposed sheets:\n"
            f"expected {expected_outlines!r}\nactual {two_up_outlines!r}"
        )

    expected_metadata = expected_publication_metadata(config)
    actual_metadata = pdf_info_fields(two_up)
    for key in ("Title", "Author", "Subject", "Keywords"):
        if actual_metadata.get(key, "") != expected_metadata[key]:
            fail(
                f"{two_up.name} {key.lower()} metadata is "
                f"{actual_metadata.get(key, '')!r}; expected "
                f"{expected_metadata[key]!r}"
            )
    if actual_metadata.get("Tagged", "").lower() != "no":
        fail(f"{two_up.name} must remain an explicitly untagged print derivative")

    catalog = pdf_catalog(two_up)
    language = catalog.get("/Lang")
    if language not in {
        expected_metadata["Language"],
        f"u:{expected_metadata['Language']}",
    }:
        fail(
            f"{two_up.name} language metadata is {language!r}; expected "
            f"{expected_metadata['Language']!r}"
        )
    for structural_key in ("/MarkInfo", "/StructTreeRoot"):
        if structural_key in catalog:
            fail(
                f"{two_up.name} copied the source tagging claim: {structural_key}"
            )
    xmp = run("pdfinfo", "-meta", str(two_up), cwd=two_up.parent).lower()
    for claim in ("pdfaid:", "pdfuaid:"):
        if claim in xmp:
            fail(f"{two_up.name} incorrectly claims {claim[:-1]} conformance")


def assert_pdf_type_area(
    path: Path,
    expected_margins: tuple[tuple[float, float], tuple[float, float]],
) -> None:
    """Verify the 140 mm measure and KOMA's recto/verso margin allocation."""
    marker_pairs = (
        (ODD_AREA_LEFT, ODD_AREA_RIGHT),
        (EVEN_AREA_LEFT, EVEN_AREA_RIGHT),
    )
    page_width_mm, page_height_mm = pdf_page_size_mm(path)
    for index, ((left_marker, right_marker), (left_mm, right_mm)) in enumerate(
        zip(marker_pairs, expected_margins),
        start=1,
    ):
        left_page, left, _ = pdf_marker_bounds(path, left_marker)
        right_page, _, right = pdf_marker_bounds(path, right_marker)
        expected_parity = 1 if index == 1 else 0
        if left_page != right_page or left_page % 2 != expected_parity:
            fail(f"{path.name} type-area markers are not on the expected page")
        expected_left = left_mm * PDF_POINTS_PER_MM
        expected_right = right_mm * PDF_POINTS_PER_MM
        measured_right = page_width_mm * PDF_POINTS_PER_MM - right
        measured_width = right - left
        expected_width = 140 * PDF_POINTS_PER_MM
        if abs(left - expected_left) > 2.5:
            fail(
                f"{path.name} left margin is {left / PDF_POINTS_PER_MM:.1f} mm; "
                f"expected {left_mm:.1f} mm"
            )
        if abs(measured_right - expected_right) > 2.5:
            fail(
                f"{path.name} right margin is "
                f"{measured_right / PDF_POINTS_PER_MM:.1f} mm; "
                f"expected {right_mm:.1f} mm"
            )
        if abs(measured_width - expected_width) > 3:
            fail(
                f"{path.name} text measure is "
                f"{measured_width / PDF_POINTS_PER_MM:.1f} mm; expected 140.0 mm"
            )

    top_page, _, top, _, _ = pdf_marker_box(path, EVEN_AREA_LEFT)
    bottom_page, _, _, _, bottom = pdf_marker_box(path, BOTTOM_AREA_LEFT)
    if top_page != bottom_page:
        fail(f"{path.name} vertical type-area markers are not on one page")
    measured_top = top / PDF_POINTS_PER_MM
    measured_bottom = page_height_mm - bottom / PDF_POINTS_PER_MM
    # Marker glyph bounds extend beyond their baselines; the larger faithful
    # body size needs slightly more tolerance than the former 12 pt probe.
    if abs(measured_top - 70 / 3) > 2.0:
        fail(f"{path.name} top margin is {measured_top:.1f} mm; expected 23.3 mm")
    if abs(measured_bottom - 140 / 3) > 2.0:
        fail(
            f"{path.name} bottom margin is {measured_bottom:.1f} mm; "
            "expected 46.7 mm"
        )


def assert_pdf_body_leading(path: Path) -> None:
    """Verify the effective baseline produced by KOMA and setspace."""
    first_page, _, first_top, _, _ = pdf_marker_box(path, BASELINE_FIRST)
    second_page, _, second_top, _, _ = pdf_marker_box(path, BASELINE_SECOND)
    if first_page != second_page:
        fail(f"{path.name} baseline markers are not on the same page")
    measured = second_top - first_top
    if abs(measured - 19.3) > 0.5:
        fail(
            f"{path.name} body leading is {measured:.2f} pt; "
            "expected approximately 19.3 pt"
        )


def assert_pdf_footnote_typography(path: Path) -> None:
    """Verify note size and leading relative to the 15.25 pt body."""
    first_page, _, first_top, _, first_bottom = pdf_marker_box(path, FOOTNOTE_FIRST)
    second_page, _, second_top, _, _ = pdf_marker_box(path, FOOTNOTE_SECOND)
    if first_page != second_page:
        fail(f"{path.name} footnote fixture is split unexpectedly")
    measured_leading = second_top - first_top
    if abs(measured_leading - 16) > 0.5:
        fail(
            f"{path.name} footnote leading is {measured_leading:.2f} pt; "
            "expected approximately 16 pt"
        )

    _, _, body_top, _, body_bottom = pdf_marker_box(path, BASELINE_FIRST)
    footnote_height = first_bottom - first_top
    body_height = body_bottom - body_top
    size_ratio = footnote_height / body_height
    if not 0.78 <= size_ratio <= 0.88:
        fail(
            f"{path.name} footnote-to-body glyph ratio is {size_ratio:.2f}; "
            "expected approximately 12.7/15.25"
        )


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
        "word/theme/theme1.xml",
    }
    with ZipFile(path) as archive:
        if corrupt := archive.testzip():
            fail(f"DOCX contains a corrupt member: {corrupt}")
        if missing := required - set(archive.namelist()):
            fail(f"DOCX is missing package members: {', '.join(sorted(missing))}")
        document = ET.fromstring(archive.read("word/document.xml"))
        styles = ET.fromstring(archive.read("word/styles.xml"))
        theme = ET.fromstring(archive.read("word/theme/theme1.xml"))
        footnotes = ET.fromstring(archive.read("word/footnotes.xml"))
        custom_properties = ET.fromstring(archive.read("docProps/custom.xml"))
        application_properties = ET.fromstring(archive.read("docProps/app.xml"))
        word_xml_parts = {
            name: ET.fromstring(archive.read(name))
            for name in archive.namelist()
            if name.startswith("word/") and name.endswith(".xml")
        }
        private_path_hits = {
            private_path
            for private_path in (str(LIBRARY), str(STYLE))
            if any(
                private_path.encode() in archive.read(name)
                for name in archive.namelist()
            )
        }
        media = {
            name for name in archive.namelist() if name.startswith("word/media/")
        }

    document_text = xml_text(document)
    assert_order(
        document_text,
        [
            title,
            FRONT_MARKER,
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

    rendered_headings: set[str] = set()
    for paragraph in document.iter(qn("p")):
        styles_in_paragraph = attribute_values(paragraph, "pStyle", "val")
        heading_styles = {
            style for style in styles_in_paragraph if re.fullmatch(r"Heading[1-9]", style)
        }
        if not heading_styles:
            continue
        heading = xml_text(paragraph).strip()
        rendered_headings.add(heading)
        if re.match(r"^\d+(?:\.\d+)*[.)]?\s+", heading):
            fail(f"DOCX rendered a numbered heading: {heading!r}")
        if any(node.tag == qn("numPr") for node in paragraph.iter()):
            fail(f"DOCX attached numbering properties to a heading: {heading!r}")
        if "SectionNumber" in attribute_values(paragraph, "rStyle", "val"):
            fail(f"DOCX attached a section number run to a heading: {heading!r}")
    for heading in ("Introduction", SECTION_HEADING, "Conclusion", "Bibliography"):
        if heading not in rendered_headings:
            fail(f"DOCX is missing the unnumbered heading: {heading!r}")

    toc_instructions = [
        node.text or "" for node in document.iter(qn("instrText"))
        if "TOC" in (node.text or "")
    ]
    if len(toc_instructions) != 1 or '\\o "1-1"' not in toc_instructions[0]:
        fail("DOCX TOC field must include chapter headings only")

    for name, root in word_xml_parts.items():
        for fonts in root.iter(qn("rFonts")):
            for slot in ("ascii", "hAnsi"):
                value = fonts.get(qn(slot))
                if value is not None and value != "EB Garamond":
                    fail(
                        f"DOCX uses a non-EB-Garamond Latin font in {name}: "
                        f"{value}"
                    )
            for slot in ("asciiTheme", "hAnsiTheme"):
                if fonts.get(qn(slot)) is not None:
                    fail(f"DOCX retains a Latin theme font in {name}: {slot}")
    theme_ns = f"{{{DRAWING_NS}}}"
    for family in ("majorFont", "minorFont"):
        node = theme.find(f".//{theme_ns}{family}/{theme_ns}latin")
        if node is None or node.get("typeface") != "EB Garamond":
            fail(f"DOCX {family} Latin theme must use EB Garamond")

    paragraph_styles = {
        node.get(qn("styleId")): node
        for node in styles.iter(qn("style"))
        if node.get(qn("type")) == "paragraph"
    }
    normal_style = paragraph_styles.get("Normal")
    widow_control = None if normal_style is None else normal_style.find(
        f"./{qn('pPr')}/{qn('widowControl')}"
    )
    widow_value = (
        None if widow_control is None else widow_control.get(qn("val"))
    )
    if widow_control is None or (widow_value or "").lower() in {
        "0",
        "false",
        "off",
    }:
        fail("DOCX Normal style must enable widow and orphan control")
    body_style = paragraph_styles.get("BodyText")
    body_base = None if body_style is None else body_style.find(qn("basedOn"))
    if body_base is None or body_base.get(qn("val")) != "Normal":
        fail("DOCX Body Text must inherit widow control from the Normal style")

    custom_property_names = {
        node.get("name")
        for node in custom_properties.iter()
        if node.tag.rsplit("}", 1)[-1] == "property"
    }
    if private_properties := {"bibliography", "csl"} & custom_property_names:
        fail(
            "DOCX retained private citation properties: "
            + ", ".join(sorted(private_properties))
        )
    if private_path_hits:
        fail(
            "DOCX package leaked local citation paths: "
            + ", ".join(sorted(private_path_hits))
        )

    stale_statistics = {
        "Pages",
        "Words",
        "Characters",
        "CharactersWithSpaces",
        "Paragraphs",
        "Lines",
        "TotalTime",
    }
    packaged_statistics = {
        node.tag.rsplit("}", 1)[-1] for node in application_properties.iter()
    }
    if leaked_statistics := stale_statistics & packaged_statistics:
        fail(
            "DOCX copied stale reference-document statistics: "
            + ", ".join(sorted(leaked_statistics))
        )

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

    with tempfile.TemporaryDirectory(prefix="longform-docx-sanitize-") as area:
        sanitized_again = Path(area) / path.name
        run(
            QUARTO,
            "pandoc",
            "lua",
            str(ROOT / "publishing/docx/sanitize.lua"),
            str(path),
            str(sanitized_again),
            cwd=ROOT,
        )
        if sanitized_again.read_bytes() != path.read_bytes():
            fail("DOCX package sanitization is not byte-for-byte idempotent")


def assert_headed_front_matter(project: Path) -> None:
    """Confirm the adapter filter leaves an authored front-matter H1 intact."""
    with tempfile.TemporaryDirectory(prefix="longform-headed-front-") as area:
        source = Path(area) / "front-matter.md"
        source.write_text(
            "# Preface {.unnumbered}\n\n"
            "Integration fixture: the headed front matter is present.\n",
            encoding="utf-8",
        )
        command = (QUARTO, "pandoc", str(source), "--from", "markdown", "--to", "json")
        baseline = json.loads(run(*command, cwd=project))
        filtered = json.loads(
            run(
                *command,
                "--lua-filter",
                str(project / "publishing/filters/front-matter.lua"),
                cwd=project,
            )
        )
        if filtered != baseline:
            fail("front-matter filter modified an authored heading")


def assert_real_pdf_standards(path: Path, verifier: str | None) -> None:
    """Validate the generated fixture with CI's real veraPDF executable."""
    if verifier is None:
        return
    result = subprocess.run(
        (verifier, "-f", "4f", str(path)),
        cwd=path.parent,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    output = result.stdout or ""
    compliance = re.findall(r'isCompliant=["\'](true|false)["\']', output)
    if result.returncode != 0:
        fail(f"real veraPDF profile 4f exited with {result.returncode}:\n{output}")
    if not compliance:
        fail(f"real veraPDF profile 4f returned no explicit result:\n{output}")
    if any(value == "false" for value in compliance):
        fail(f"fixture PDF is not compliant with veraPDF profile 4f:\n{output}")
    progress("real veraPDF profile 4f passed")


def assert_strict_pdf_validation_fails_closed(
    project: Path,
    environment: dict[str, str],
) -> None:
    """A non-compliant veraPDF report must stop before output promotion."""
    mathml_sidecar = project / "index-luamml-mathml.html"
    mathml_sidecar.write_text(
        "sentinel for failed-build cleanup\n",
        encoding="utf-8",
    )
    verifier = Path(environment["QUARTO_VERAPDF"])
    if verifier.parent != project / "tool shims":
        fail("refusing to replace a veraPDF executable outside the test shims")
    verifier.write_text(
        "#!/bin/sh\n"
        "printf '%s\\n' '<validationReport isCompliant=\"false\"/>'\n",
        encoding="utf-8",
    )
    verifier.chmod(0o755)
    result = subprocess.run(
        (QUARTO, "run", "publishing/longform.ts", "build"),
        cwd=project,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=environment,
    )
    if result.returncode == 0:
        fail("strict PDF validation accepted a non-compliant veraPDF report")
    if "veraPDF validation failed for profile 4f" not in result.stdout:
        fail(
            "strict PDF validation failed without the expected diagnostic:\n"
            f"{result.stdout}"
        )
    if mathml_sidecar.exists():
        fail("failed build retained tagged LuaLaTeX's MathML sidecar")


def assert_gfm(path: Path, title: str, subtitle: str, config: dict) -> None:
    require_file(path)
    text = path.read_text(encoding="utf-8")
    subtitle_text = plain_metadata_text(subtitle)
    title_line = f"# {title}"
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        fail("GFM must begin with discovery metadata")
    try:
        metadata_end = lines.index("---", 1)
    except ValueError:
        fail("GFM discovery metadata is not terminated")
    metadata: dict[str, object] = {}
    for line in lines[1:metadata_end]:
        key, separator, value = line.partition(":")
        if not separator:
            fail(f"GFM discovery metadata has an invalid line: {line!r}")
        try:
            metadata[key] = json.loads(value.strip())
        except json.JSONDecodeError as error:
            fail(f"GFM discovery metadata is not JSON-safe: {line!r}: {error}")

    book = config.get("book", {})
    if not isinstance(book, dict):
        book = {}
    identity = expected_publication_metadata(config)
    raw_keywords = config.get("keywords", [])
    expected_keywords = (
        [plain_metadata_text(item) for item in raw_keywords]
        if isinstance(raw_keywords, list)
        else [plain_metadata_text(raw_keywords)]
    )
    expected_fields: list[tuple[str, object]] = [
        ("title", plain_metadata_text(book.get("title", ""))),
        ("subtitle", subtitle_text),
        ("title-meta", identity["Title"]),
        ("author", identity["Author"]),
        ("date", plain_metadata_text(book.get("date", ""))),
        ("lang", identity["Language"]),
        ("subject", identity["Subject"]),
        ("keywords", list(filter(None, expected_keywords))),
    ]
    expected_metadata = {
        key: value
        for key, value in expected_fields
        if (isinstance(value, list) and value)
        or (not isinstance(value, list) and value != "")
    }
    if metadata != expected_metadata:
        fail(
            "GFM discovery metadata differs:\n"
            f"expected {expected_metadata!r}\nactual {metadata!r}"
        )

    body_text = "\n".join(lines[metadata_end + 1 :])
    if lines.count(title_line) != 1:
        fail("GFM must contain exactly one document-title H1")
    title_index = lines.index(title_line)
    following = [line for line in lines[title_index + 1 :] if line.strip()]
    raw_authors = book.get("author", [])
    visible_authors = (
        [plain_metadata_text(author) for author in raw_authors]
        if isinstance(raw_authors, list)
        else [plain_metadata_text(raw_authors)]
    )
    expected_title_block = []
    if subtitle_text:
        expected_title_block.append(f"*{subtitle_text}*")
    expected_title_block.extend(filter(None, visible_authors))
    date_text = plain_metadata_text(book.get("date", ""))
    if date_text:
        expected_title_block.append(date_text)
    if following[: len(expected_title_block)] != expected_title_block:
        fail(
            "GFM title block does not contain subtitle, author, and date in order: "
            f"{following[:len(expected_title_block)]!r}"
        )
    if subtitle_text:
        if body_text.count(subtitle_text) != 1:
            fail("GFM body must preserve the visible subtitle exactly once")
        if re.search(rf"(?m)^#+\s+.*{re.escape(subtitle_text)}", body_text):
            fail("GFM must not render the subtitle as a heading")
    elif "**" in following[:1]:
        fail("GFM rendered an empty subtitle paragraph")

    assert_order(
        text,
        [
            FRONT_MARKER,
            "# Introduction",
            INTRO_MARKER,
            "# Conclusion",
            GFM_MARKER,
            PROFILE_MARKER,
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
        "\\pdfbookmark",
    ):
        if leaked in text:
            fail(f"GFM contains unprocessed source markup: {leaked!r}")

    alt_pattern = r"\s+".join(map(re.escape, FIGURE_ALT.split()))
    markdown_image = re.search(rf"!\[{alt_pattern}\]\(([^)]+)\)", text)
    target = None
    if markdown_image is not None:
        destination = markdown_image.group(1).strip()
        if destination.startswith("<") and ">" in destination:
            target = destination[1 : destination.index(">")]
        else:
            target = destination.split(maxsplit=1)[0]
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
    target = unquote(target)
    extracted = (path.parent / target).resolve()
    media_root = (path.parent / f"{path.stem}_files").resolve()
    if not extracted.is_relative_to(media_root) or not extracted.is_file():
        fail(f"GFM figure was not extracted beside the Markdown: {target}")
    if extracted.read_bytes() != ONE_PIXEL_PNG:
        fail("GFM extracted the wrong media bytes")


def assert_sparse_gfm_identity(
    project: Path,
    build: Path,
    environment: dict[str, str],
) -> None:
    """Exercise optional identity fields, multiple authors, and scalar keywords."""
    metadata = project / "writing/manuscript/metadata.yml"
    metadata.write_text(
        "lang: en-GB\n"
        'keywords: "fixture, scalar"\n'
        "book:\n"
        f'  output-file: "{TEST_OUTPUT}"\n'
        '  title: "Sparse Identity Fixture"\n'
        "  author:\n"
        '    - name: "Alex Example"\n'
        '    - name: "Robin Fixture"\n',
        encoding="utf-8",
    )
    routine_environment = environment.copy()
    routine_environment.pop("LONGFORM_VALIDATE_PDF", None)
    routine_environment.pop("QUARTO_VERAPDF", None)
    run(
        QUARTO,
        "run",
        "publishing/longform.ts",
        "build",
        cwd=project,
        capture=False,
        env=routine_environment,
    )
    config = inspect(project)
    output_name = config["book"]["output-file"]
    gfm = build / f"{output_name}.md"
    assert_gfm(gfm, "Sparse Identity Fixture", "", config)
    assert_no_intermediates(project, build)


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
    if (project / "index-luamml-mathml.html").exists():
        fail("build retained tagged LuaLaTeX's MathML sidecar")


def resolve_from(base: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def assert_zettlr(project: Path, config: dict) -> None:
    run(
        QUARTO,
        "run",
        "publishing/longform.ts",
        "zettlr",
        cwd=project,
        capture=False,
    )
    generated = project / "writing/.ztr-directory"
    require_file(generated)
    if generated.is_symlink():
        fail("writing/.ztr-directory must be a generated regular file")
    payload = json.loads(generated.read_text(encoding="utf-8"))
    zettlr_project = payload.get("project", {})

    expected_files: list[Path] = []
    for chapter in config.get("book", {}).get("chapters", []):
        if chapter == "index.md":
            expected_files.append(
                (project / "writing/manuscript/front-matter.md").resolve()
            )
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
    for relative in (
        "_quarto.yml.local",
        "_quarto-profile.local",
        "writing/.ztr-directory",
    ):
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
    assert_copy_project_boundaries()
    real_verapdf = incoming_real_verapdf()
    with tempfile.TemporaryDirectory(prefix="longform-kit-test-") as test_area:
        project = Path(test_area) / "project with spaces"
        copy_project(project)
        write_local_configuration(project)
        write_test_manuscript(project)
        assert_default_custom_profile(project)
        write_test_profile(project)
        build_environment, qpdf_marker, verapdf_marker = write_tool_shims(project)
        config = assert_configuration(project)
        progress("configuration verified; rendering four outputs")

        build = project / config.get("project", {}).get("output-dir", "output")
        output_name = config["book"]["output-file"]
        retired_pdfs = (
            build / f"{output_name}-binding.pdf",
            build / f"{output_name}-binding-2up.pdf",
        )
        build.mkdir(parents=True, exist_ok=True)
        for retired in retired_pdfs:
            retired.write_bytes(b"%PDF-1.0\nretired binding-suffix output\n")
        (project / "index-luamml-mathml.html").write_text(
            "sentinel for successful-build cleanup\n",
            encoding="utf-8",
        )

        run(
            QUARTO,
            "run",
            "publishing/longform.ts",
            "build",
            cwd=project,
            capture=False,
            env=build_environment,
        )
        qpdf_invocations = qpdf_marker.read_text(encoding="utf-8")
        if re.search(r"(?m)^--version$", qpdf_invocations) is None:
            fail("build did not check the configured qpdf version")
        if "--json --json-key=outlines" not in qpdf_invocations:
            fail("build did not use the QPDF override to read source bookmarks")
        verapdf_invocations = verapdf_marker.read_text(encoding="utf-8")
        if re.search(r"(?:^|\s)-f\s+4f(?:\s|$)", verapdf_invocations) is None:
            fail("strict PDF validation did not request veraPDF profile 4f")
        if re.search(r"(?:^|\s)-f\s+ua2(?:\s|$)", verapdf_invocations):
            fail("PDF/A-only configuration unexpectedly requested the ua2 profile")
        progress("build command completed; inspecting artifacts")
        pdf = build / f"{output_name}.pdf"
        two_up_pdf = build / f"{output_name}-2up.pdf"
        docx = build / f"{output_name}.docx"
        gfm = build / f"{output_name}.md"
        for artifact in (pdf, two_up_pdf, docx, gfm):
            require_file(artifact)
        for retired in retired_pdfs:
            if retired.exists():
                fail(f"build retained a retired binding-suffix PDF: {retired.name}")

        pdf_text, pdf_pages = assert_pdf(pdf)
        assert_real_pdf_standards(pdf, real_verapdf)
        assert_pdf_body_leading(pdf)
        assert_pdf_footnote_typography(pdf)
        assert_pdf_type_area(
            pdf,
            expected_margins=((70 / 3, 140 / 3), (140 / 3, 70 / 3)),
        )
        title = config.get("book", {}).get("title", "A Longform Document")
        assert_two_up_pdf(
            pdf,
            two_up_pdf,
            pdf_text,
            pdf_pages,
            title,
            config,
        )
        headings = ("Introduction", "Conclusion", "Bibliography")
        heading_pages = pdf_heading_pages(pdf, headings)
        for heading, page in heading_pages.items():
            if page % 2 == 0:
                fail(
                    "PDF chapter did not begin on a recto page: "
                    f"{heading!r}"
                )
        progress("PDF and two-up PDF verified")

        assert_docx(docx, title)
        progress("DOCX verified")
        subtitle = config.get("book", {}).get("subtitle", "")
        assert_gfm(gfm, title, subtitle, config)
        progress("combined GFM verified")
        assert_no_intermediates(project, build)
        assert_zettlr(project, config)
        progress("Zettlr configuration verified")
        assert_headed_front_matter(project)
        progress("headed front matter verified")
        assert_sparse_gfm_identity(project, build, build_environment)
        progress("sparse and multi-author GFM identity verified")
        assert_strict_pdf_validation_fails_closed(project, build_environment)
        progress("strict PDF validation failure verified")


if __name__ == "__main__":
    try:
        test_build()
    except (AssertionError, OSError, ValueError, BadZipFile) as error:
        print(f"test_build: {error}", file=sys.stderr)
        raise SystemExit(1)
    print("test_build: all Longform Kit outputs passed structural verification")
