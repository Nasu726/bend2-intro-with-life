#!/usr/bin/env python3
"""Compare regenerated reader materials to committed ones, ignoring PDF metadata.

The checked-in PDF/ZIP must have identical rendered text; the other ZIP files
must be byte-for-byte equal. Binary PDF equality is not reliable *across PDF builds* because of creation
timestamps, but each ZIP must contain the exact standalone PDF from its own
edition.
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

def cover_pixels(data: bytes) -> bytes:
    """Render page 1 to catch cover artwork changes invisible to pdftotext."""
    cp = subprocess.run(
        ["pdftoppm", "-f", "1", "-l", "1", "-singlefile",
         "-r", "72", "-png", "-"],
        input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return cp.stdout

def compare_reader_zips(old_archive: bytes, new_archive: bytes,
                        old_pdf: bytes, new_pdf: bytes) -> None:
    """Check contents, including exact PDF bytes within each edition's ZIP.

    We deliberately do not compare ZIP container bytes: DEFLATE headers and
    metadata can vary while the reader-facing files remain identical.
    """
    with zipfile.ZipFile(BytesIO(old_archive)) as older, \
         zipfile.ZipFile(BytesIO(new_archive)) as newer:
        old_names, new_names = older.namelist(), newer.namelist()
        if len(old_names) != len(set(old_names)) or len(new_names) != len(set(new_names)):
            raise AssertionError("Reader ZIP has duplicate entry names")
        if set(old_names) != set(new_names):
            raise AssertionError("Reader ZIP file list changed")
        pdf_names = [name for name in old_names if name.endswith("/textbook.pdf")]
        if len(pdf_names) != 1:
            raise AssertionError("Reader ZIP must contain exactly one textbook.pdf")
        pdf_name = pdf_names[0]
        for name in old_names:
            prev, cur = older.read(name), newer.read(name)
            if name == pdf_name:
                if prev != old_pdf:
                    raise AssertionError("Committed ZIP PDF differs from committed standalone PDF")
                if cur != new_pdf:
                    raise AssertionError("Regenerated ZIP PDF differs from regenerated standalone PDF")
            elif prev != cur:
                raise AssertionError(f"Reader ZIP file changed: {name}")


def main() -> None:
    old_pdf, new_pdf = committed(PDF), (ROOT / PDF).read_bytes()
    old_text, new_text = text_of_pdf(old_pdf), text_of_pdf(new_pdf)
    if old_text != new_text:
        raise AssertionError("Reader-facing PDF text differs from committed PDF")
    # A visually changed cover can have identical extractable text. Check the
    # raster too, using the same Poppler binary for both PDFs.
    new_cover = cover_pixels(new_pdf)
    if cover_pixels(old_pdf) != new_cover:
        raise AssertionError("Reader-facing PDF cover differs from committed PDF")
    if not old_text or len(old_text) < 5000:
        raise AssertionError("PDF has unexpectedly little extractable content")
    compare_reader_zips(committed(ZIP), (ROOT / ZIP).read_bytes(), old_pdf, new_pdf)
    print("PASS: PDF text, cover pixels, exact embedded PDF bytes and learner ZIP entries match")

if __name__ == "__main__":
    try:
        main()
    except (OSError, subprocess.CalledProcessError, AssertionError, zipfile.BadZipFile) as e:
        sys.exit(f"FAILED: {e}")
