#!/usr/bin/env python3
"""Optionally populate generated DOCX TOC fields through LibreOffice.

Register this as a Quarto post-render hook. It is a no-op unless
LONGFORM_REFRESH_DOCX_TOC=1, so ordinary and CI builds do not acquire a
LibreOffice dependency. When enabled, it updates DOCX files listed by Quarto
before Longform Kit promotes them from its staging directory.
"""

import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time


def output_docx_files():
    listed = os.environ.get("QUARTO_PROJECT_OUTPUT_FILES", "")
    return [
        (Path.cwd() / item).resolve()
        for item in listed.splitlines()
        if item.strip().lower().endswith(".docx")
    ]


def property_value(PropertyValue, name, value):
    item = PropertyValue()
    item.Name = name
    item.Value = value
    return item


def available_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def main():
    paths = output_docx_files()
    if os.environ.get("LONGFORM_REFRESH_DOCX_TOC") != "1" or not paths:
        return
    executable = shutil.which("libreoffice") or shutil.which("soffice")
    if not executable:
        raise RuntimeError("DOCX TOC refresh requires LibreOffice")

    try:
        import uno
        from com.sun.star.beans import PropertyValue
    except ImportError as error:
        raise RuntimeError(
            "DOCX TOC refresh requires LibreOffice's Python UNO module"
        ) from error

    with tempfile.TemporaryDirectory(prefix="longform-libreoffice-") as profile:
        port = available_port()
        process = subprocess.Popen(
            [
                executable,
                f"-env:UserInstallation={Path(profile).as_uri()}",
                "--headless",
                "--nologo",
                "--nodefault",
                "--nofirststartwizard",
                f"--accept=socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            local = uno.getComponentContext()
            resolver = local.ServiceManager.createInstanceWithContext(
                "com.sun.star.bridge.UnoUrlResolver", local
            )
            office = None
            for _ in range(100):
                try:
                    office = resolver.resolve(
                        f"uno:socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext"
                    )
                    break
                except Exception:
                    time.sleep(0.1)
            if office is None:
                raise RuntimeError("LibreOffice UNO listener did not start")

            desktop = office.ServiceManager.createInstanceWithContext(
                "com.sun.star.frame.Desktop", office
            )
            for source in paths:
                document = desktop.loadComponentFromURL(
                    uno.systemPathToFileUrl(str(source)),
                    "_blank",
                    0,
                    (
                        property_value(PropertyValue, "Hidden", True),
                        property_value(PropertyValue, "ReadOnly", False),
                    ),
                )
                if document is None:
                    raise RuntimeError(f"LibreOffice could not open {source}")
                temporary = source.with_name(f".{source.stem}-toc-refresh.docx")
                try:
                    indexes = document.getDocumentIndexes()
                    for index in range(indexes.getCount()):
                        indexes.getByIndex(index).update()
                    document.storeAsURL(
                        uno.systemPathToFileUrl(str(temporary)),
                        (
                            property_value(
                                PropertyValue, "FilterName", "Office Open XML Text"
                            ),
                            property_value(PropertyValue, "Overwrite", True),
                        ),
                    )
                    document.close(True)
                    temporary.replace(source)
                finally:
                    if temporary.exists():
                        temporary.unlink()
            desktop.terminate()
        finally:
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=10)


if __name__ == "__main__":
    main()
