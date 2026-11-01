"""Rendered-page checks must catch changes invisible to PDF text extraction."""
from pathlib import Path
from unittest.mock import patch
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_bundle_consistency import compare_rendered_pages, page_pixels


class PageConsistencyTests(unittest.TestCase):
    def test_accepts_same_pixels_even_if_pdf_bytes_differ(self):
        with patch("check_bundle_consistency.page_pixels", side_effect=[
                (b"cover", b"chapter", b"figure"),
                (b"cover", b"chapter", b"figure")]):
            compare_rendered_pages(b"old metadata", b"new metadata")

    def test_rejects_changed_interior_diagram(self):
        with patch("check_bundle_consistency.page_pixels", side_effect=[
                (b"cover", b"chapter", b"figure"),
                (b"cover", b"chapter", b"different figure")]):
            with self.assertRaisesRegex(AssertionError, "page 3 differs"):
                compare_rendered_pages(b"old", b"new")

    def test_rejects_page_count_change(self):
        with patch("check_bundle_consistency.page_pixels", side_effect=[
                (b"cover", b"chapter"), (b"cover",)]):
            with self.assertRaisesRegex(AssertionError, "page count changed: 2 -> 1"):
                compare_rendered_pages(b"old", b"new")

    def test_rejects_empty_render(self):
        from unittest.mock import MagicMock
        with patch("check_bundle_consistency.subprocess.run", return_value=MagicMock()):
            with self.assertRaisesRegex(AssertionError, "rendered no pages"):
                page_pixels(b"broken")


if __name__ == "__main__":
    unittest.main()
