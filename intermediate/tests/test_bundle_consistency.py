"""Regression tests for reader ZIP and standalone PDF byte-level consistency."""
from io import BytesIO
from pathlib import Path
import sys
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_bundle_consistency import compare_reader_zips

PDF_NAME = "bend2-intermediate-reader/textbook.pdf"
CODE_NAME = "bend2-intermediate-reader/examples/45_binary_file.bend"


def make_zip(pdf=b"PDF-contents", code=b"Bend code", *, compression=zipfile.ZIP_DEFLATED,
             include_pdf=True, duplicate_pdf=False, extra=None):
    output = BytesIO()
    with zipfile.ZipFile(output, "w", compression=compression) as archive:
        if include_pdf:
            archive.writestr(PDF_NAME, pdf)
            if duplicate_pdf:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    archive.writestr(PDF_NAME, pdf)
        archive.writestr(CODE_NAME, code)
        if extra is not None:
            archive.writestr("bend2-intermediate-reader/extra.txt", extra)
    return output.getvalue()


class BundleConsistencyTests(unittest.TestCase):
    def test_accepts_exact_pdf_and_same_files_with_different_zip_compression(self):
        old = make_zip(compression=zipfile.ZIP_STORED)
        new = make_zip(compression=zipfile.ZIP_DEFLATED)
        compare_reader_zips(old, new, b"PDF-contents", b"PDF-contents")

    def test_accepts_changed_pdf_metadata_when_each_zip_contains_its_own_pdf(self):
        old = make_zip(pdf=b"PDF-contents-2026-10-17")
        new = make_zip(pdf=b"PDF-contents-2026-10-18")
        compare_reader_zips(old, new, b"PDF-contents-2026-10-17", b"PDF-contents-2026-10-18")

    def test_rejects_regenerated_zip_pdf_that_only_matches_extracted_text(self):
        old = make_zip()
        new = make_zip(pdf=b"PDF-contents-wrong-metadata")
        with self.assertRaisesRegex(AssertionError, "Regenerated ZIP PDF differs"):
            compare_reader_zips(old, new, b"PDF-contents", b"PDF-contents")

    def test_rejects_committed_zip_pdf_drift(self):
        old = make_zip(pdf=b"old-inconsistent")
        new = make_zip()
        with self.assertRaisesRegex(AssertionError, "Committed ZIP PDF differs"):
            compare_reader_zips(old, new, b"PDF-contents", b"PDF-contents")

    def test_rejects_missing_pdf(self):
        old = make_zip(include_pdf=False)
        with self.assertRaisesRegex(AssertionError, "exactly one textbook.pdf"):
            compare_reader_zips(old, old, b"PDF-contents", b"PDF-contents")

    def test_rejects_duplicate_pdf_entry(self):
        old = make_zip(duplicate_pdf=True)
        with self.assertRaisesRegex(AssertionError, "duplicate entry names"):
            compare_reader_zips(old, old, b"PDF-contents", b"PDF-contents")

    def test_rejects_modified_example(self):
        old = make_zip(code=b"original")
        new = make_zip(code=b"changed")
        with self.assertRaisesRegex(AssertionError, "Reader ZIP file changed"):
            compare_reader_zips(old, new, b"PDF-contents", b"PDF-contents")

    def test_rejects_added_example(self):
        old = make_zip()
        new = make_zip(extra=b"not expected")
        with self.assertRaisesRegex(AssertionError, "Reader ZIP file list changed"):
            compare_reader_zips(old, new, b"PDF-contents", b"PDF-contents")


if __name__ == "__main__":
    unittest.main()
