"""Small synthetic fixtures for extraction fidelity and honest access limits."""
import hashlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import fitz
from PIL import Image, ImageDraw
from docx import Document

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("read_documents", ROOT / "skills/write-innovation-essays/scripts/read_documents.py")
reader = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reader)


class DocumentIntake(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def native_pdf(self):
        path = self.root / "source.pdf"
        with fitz.open() as doc:
            doc.new_page().insert_text((50, 50), "A synthetic native text page with enough characters for extraction.")
            doc.new_page().insert_text((50, 50), "The second source page remains separate and ordered.")
            doc.save(path)
        return path

    def image_pdf(self):
        image = Image.new("RGB", (500, 160), "white")
        ImageDraw.Draw(image).text((20, 30), "Synthetic image page", fill="black")
        stream = io.BytesIO()
        image.save(stream, format="PNG")
        path = self.root / "scan.pdf"
        with fitz.open() as doc:
            page = doc.new_page(width=500, height=160)
            page.insert_image(page.rect, stream=stream.getvalue())
            doc.save(path)
        return path

    def test_native_pages_rendered_and_source_unchanged(self):
        path = self.native_pdf()
        before = path.read_bytes()
        result = reader.extract(path, self.root / "out", render_pages=True)
        self.assertEqual(result["status"], "extracted_not_read")
        self.assertFalse(result["human_or_agent_read_performed"])
        self.assertEqual(result["page_count"], 2)
        self.assertEqual([p["page"] for p in result["pages"]], [1, 2])
        text = Path(result["text_file"]).read_text()
        self.assertLess(text.index("A synthetic"), text.index("The second"))
        output = Path(result["manifest_file"]).parent
        for page in result["pages"]:
            with Image.open(output / page["rendered_page"]) as image:
                image.verify()
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(result["source"]["sha256"], hashlib.sha256(before).hexdigest())

    def test_image_page_reports_gap_without_automatic_ocr(self):
        result = reader.extract(self.image_pdf(), self.root / "out")
        page = result["pages"][0]
        self.assertEqual(page["native_nonwhitespace_characters"], 0)
        self.assertIn("no_native_text", page["flags"])
        self.assertFalse(page["ocr"]["requested"])
        self.assertEqual(result["ocr_engine"]["status"], "not_requested")
        self.assertTrue(result["extraction_gaps"])

    def test_missing_ocr_engine_is_explicit(self):
        with patch.object(reader.shutil, "which", return_value=None):
            result = reader.extract(self.image_pdf(), self.root / "out", ocr=True)
        self.assertEqual(result["pages"][0]["ocr"]["status"], "unavailable")
        self.assertEqual(result["status"], "extracted_not_read")
        self.assertNotIn("accuracy_validated", result["pages"][0]["ocr"])

    def test_docx_preserves_table_between_paragraphs(self):
        path = self.root / "ordered.docx"
        doc = Document()
        doc.add_paragraph("Before the table")
        table = doc.add_table(rows=1, cols=2)
        table.cell(0, 0).text = "Cell A"
        table.cell(0, 1).text = "Cell B"
        doc.add_paragraph("After the table")
        doc.sections[0].footer.paragraphs[0].text = "Footer source text"
        doc.save(path)
        before = path.read_bytes()
        result = reader.extract(path, self.root / "out", include_headers_footers=True)
        self.assertEqual([b["type"] for b in result["body_blocks"]], ["paragraph", "table", "paragraph"])
        text = Path(result["text_file"]).read_text()
        self.assertLess(text.index("Before"), text.index("Cell A"))
        self.assertLess(text.index("Cell B"), text.index("After"))
        self.assertIn("Footer source text", text)
        self.assertIsNone(result["page_count"])
        self.assertEqual(path.read_bytes(), before)

    def test_unsafe_zip_members_inventoried_never_extracted(self):
        path = self.root / "members.zip"
        with zipfile.ZipFile(path, "w") as archive:
            for name in ["../escape.txt", "/absolute.txt", "C:\\unsafe.txt", "safe/note.txt"]:
                archive.writestr(name, "synthetic source")
        result = reader.extract(path, self.root / "out")
        self.assertEqual(result["member_count"], 4)
        self.assertEqual(sum(m["unsafe_path"] for m in result["members"]), 3)
        self.assertEqual(result["extraction_state"], "inventory_only")
        self.assertFalse(result["archive_contents_extracted"])
        self.assertFalse((self.root / "escape.txt").exists())
        self.assertFalse((self.root / "out/safe").exists())

    def test_utf8_is_strict_instead_of_guessing_or_replacing(self):
        path = self.root / "bad.md"
        path.write_bytes(b"Valid prefix\xffinvalid")
        result = reader.extract(path, self.root / "out")
        self.assertEqual(result["status"], "extracted_not_read")
        self.assertEqual(result["extraction_state"], "unavailable")
        self.assertNotIn("text_file", result)
        self.assertIn("utf-8", result["error"].lower())


if __name__ == "__main__":
    unittest.main()
