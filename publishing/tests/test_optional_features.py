#!/usr/bin/env python3
"""Verify the optional-feature catalogue and documentation contract."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FEATURES = ROOT / "publishing/features"
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


if __name__ == "__main__":
    try:
        test_contract()
    except (AssertionError, OSError) as error:
        print(f"test_optional_features: {error}")
        raise SystemExit(1)
    print("test_optional_features: contract passed")
