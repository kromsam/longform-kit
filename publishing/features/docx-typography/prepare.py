#!/usr/bin/env python3
"""Apply the optional publication DOCX design before TOC refresh."""

from pathlib import Path
import sys

sys.dont_write_bytecode = True

from policy import configure_generated, listed_docx_files


def main() -> None:
    paths = [Path(item).resolve() for item in sys.argv[1:]] or listed_docx_files()
    for path in paths:
        if path.suffix.lower() == ".docx":
            configure_generated(path)


if __name__ == "__main__":
    main()
