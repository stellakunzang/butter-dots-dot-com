"""
PDF extraction QA tests.

Regression suite for the broken-CMap detection + OCR fallback path.
The fixture PDF (Bodhisattva Vow Downfalls) is a Word-generated document using
the Microsoft Himalaya font, whose ToUnicode CMap covers only 38 of ~140 glyphs.
Stacked Tibetan consonants are emitted as raw ASCII glyph IDs by both pdfplumber
and PyMuPDF unless the broken-CMap fallback routes the PDF through BDRC OCR.
"""
import re
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"
BODHISATTVA_VOW_PDF = FIXTURES / "bodhisattva_vow.pdf"


@pytest.fixture(scope="module")
def pdf_bytes() -> bytes:
    return BODHISATTVA_VOW_PDF.read_bytes()


@pytest.fixture(scope="module")
def extracted_pages(pdf_bytes):
    from app.pdf.extractor import extract_pdf
    pages, _ = extract_pdf(pdf_bytes)
    return pages


class TestBrokenCMapDetection:
    """The broken-CMap heuristic should fire for this PDF."""

    def test_raw_pdfplumber_has_latin_artifacts(self, pdf_bytes):
        """Confirm pdfplumber alone produces ASCII garbage for this font."""
        from app.pdf.extractor import extract_digital
        pages = extract_digital(pdf_bytes)
        all_text = " ".join(p.text for p in pages)
        latin = re.findall(r"[A-Za-z0-9]", all_text)
        assert latin, (
            "Expected pdfplumber to produce Latin artifacts for this "
            "Microsoft Himalaya PDF — if this passes the font may have been fixed"
        )

    def test_broken_cmap_detected(self, pdf_bytes):
        """_has_broken_cmap() should return True for this PDF."""
        from app.pdf.extractor import extract_digital, _has_broken_cmap
        pages = extract_digital(pdf_bytes)
        assert _has_broken_cmap(pages), (
            "Broken CMap not detected — threshold may need lowering or "
            "the PDF has been re-exported with a fixed font"
        )


class TestOCRFallbackQuality:
    """After the OCR fallback, extracted text should be clean Tibetan."""

    def test_no_latin_characters(self, extracted_pages):
        """Zero ASCII letters or digits in OCR output for a pure-Tibetan document."""
        failures = []
        for page in extracted_pages:
            bad = re.findall(r"[A-Za-z0-9]", page.text)
            if bad:
                failures.append(f"Page {page.page_number}: {bad[:20]}")
        assert not failures, (
            "Latin/digit characters found after OCR fallback:\n"
            + "\n".join(failures)
        )

    def test_has_tibetan_content(self, extracted_pages):
        """OCR output should contain actual Tibetan Unicode characters."""
        all_text = " ".join(p.text for p in extracted_pages)
        tibetan = [c for c in all_text if 0x0F00 <= ord(c) <= 0x0FFF]
        assert len(tibetan) > 100, (
            f"Too few Tibetan characters ({len(tibetan)}) — OCR may have failed entirely"
        )


class TestEndToEndSpellcheck:
    """Full pipeline: extract → spellcheck should report zero non-Tibetan tokens."""

    def test_no_non_tibetan_skipped_errors(self, pdf_bytes):
        """The spellchecker should not encounter any non-Tibetan characters."""
        from app.pdf.extractor import extract_pdf
        from app.spellcheck.engine import TibetanSpellChecker

        pages, _ = extract_pdf(pdf_bytes)
        engine = TibetanSpellChecker()

        non_tibetan_count = 0
        for page in pages:
            if not page.text.strip():
                continue
            result = engine.check_text(page.text)
            for error in result.errors:
                if error.error_type == "non_tibetan_skipped":
                    non_tibetan_count += 1

        assert non_tibetan_count == 0, (
            f"Spellchecker encountered {non_tibetan_count} non-Tibetan token(s) "
            "— OCR fallback may not be cleaning up all encoding artifacts"
        )
