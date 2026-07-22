#!/usr/bin/env python3
"""Restore deterministic publication OOXML after optional external rewriting.

The shared transform is deliberately idempotent, so this hook is safe both
after preparation alone and when an office suite rewrote styles,
relationships, section properties, or embedded font parts.
"""

from pathlib import Path
import sys

sys.dont_write_bytecode = True

from policy import listed_docx_files, stabilize_generated


def main() -> None:
    paths = [Path(item).resolve() for item in sys.argv[1:]] or listed_docx_files()
    for path in paths:
        if path.suffix.lower() == ".docx":
            stabilize_generated(path)


if __name__ == "__main__":
    main()
