#!/usr/bin/env python3
"""Compare regenerated reader materials to committed ones, ignoring PDF metadata.

The checked-in PDF/ZIP must have identical rendered text; the other ZIP files
must be byte-for-byte equal. Binary PDF equality is not reliable because of
creation timestamps and producer metadata.
"""
from __future__ import annotations
from io import BytesIO
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
PDF = Path("intermediate/Bend2を使いこなす_プレビュー.pdf")
ZIP = Path("reader-packages/bend2-intermediate-reader-preview.zip")

def committed(path: Path) -> bytes:
    return subprocess.check_output(["git", "show", f"HEAD:{path.as_posix()}"], cwd=ROOT)

def text_of_pdf(data: bytes) -> bytes:
    cp = subprocess.run(["pdftotext", "-layout", "-", "-"], input=data,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return cp.stdout

def main() -> None:
    old_pdf, new_pdf = committed(PDF), (ROOT / PDF).read_bytes()
    old_text, new_text = text_of_pdf(old_pdf), text_of_pdf(new_pdf)
    if old_text != new_text:
        raise AssertionError("Reader-facing PDF text differs from committed PDF")
    if not old_text or len(old_text) < 5000:
        raise AssertionError("PDF has unexpectedly little extractable content")
    with zipfile.ZipFile(BytesIO(committed(ZIP))) as older, \
         zipfile.ZipFile(ROOT / ZIP) as newer:
        if set(older.namelist()) != set(newer.namelist()):
            raise AssertionError("Reader ZIP file list changed")
        for name in older.namelist():
            prev, cur = older.read(name), newer.read(name)
            if name.endswith("/textbook.pdf"):
                if text_of_pdf(prev) != new_text or text_of_pdf(cur) != new_text:
                    raise AssertionError("ZIP textbook contents do not match source PDF")
            elif prev != cur:
                raise AssertionError(f"Reader ZIP file changed: {name}")
    print("PASS: PDF text and all learner ZIP entries match the committed edition")

if __name__ == "__main__":
    try:
        main()
    except (OSError, subprocess.CalledProcessError, AssertionError) as e:
        sys.exit(f"FAILED: {e}")
