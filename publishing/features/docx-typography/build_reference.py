#!/usr/bin/env python3
"""Build or verify the optional DOCX typography reference document."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode = True

from policy import configure_reference


FEATURE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FEATURE_DIR.parents[2]
DEFAULT_SOURCE = PROJECT_ROOT / "publishing" / "docx" / "reference.docx"
DEFAULT_OUTPUT = FEATURE_DIR / "reference.docx"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    source = args.source.resolve()
    output = args.output.resolve()
    if args.check:
        if not output.is_file():
            raise SystemExit(f"generated reference DOCX is missing: {output}")
        with tempfile.TemporaryDirectory(prefix="longform-docx-reference-") as directory:
            candidate = Path(directory) / "reference.docx"
            configure_reference(source, candidate)
            if candidate.read_bytes() != output.read_bytes():
                raise SystemExit(
                    "reference DOCX is stale; run "
                    "publishing/features/docx-typography/build_reference.py"
                )
        return
    configure_reference(source, output)


if __name__ == "__main__":
    main()
