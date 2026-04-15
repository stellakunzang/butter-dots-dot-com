"""
Tests for broken CMap detection and OCR fallback routing in extract_pdf.

Two corruption patterns are guarded:

  1. PUA codepoints (U+E000–U+F8FF) — fonts whose CMap is absent entirely;
     fitz returns raw glyph IDs that land in the Private Use Area.

  2. Microsoft Himalaya vowel-O phantom — Himalaya's CMap maps the vowel sign
     ོ (U+0F7C) to the three-character sequence ྐྱོ (U+0F90 + U+0FB1 + U+0F7C).
     All characters are valid Tibetan Unicode, so the PUA check misses it, but
     the phantom trigram appears dozens of times in any Himalaya document and
     produces hundreds of false-positive spelling errors.

These tests verify detection fires correctly, does not fire on clean text, and
that extract_pdf routes to OCR when either pattern is present.
"""
import io
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from app.pdf.extractor import (
    PageContent,
    _has_broken_cmap,
    _uses_broken_cmap_font,
    _HIMALAYA_VOWEL_O_PHANTOM,
    _HIMALAYA_VOWEL_O_PHANTOMS,
    BROKEN_CMAP_PUA_THRESHOLD,
    BROKEN_CMAP_HIMALAYA_VOWEL_THRESHOLD,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pages(text: str) -> list[PageContent]:
    return [PageContent(page_number=1, text=text)]


def _minimal_pdf_bytes() -> bytes:
    """A valid single-page PDF with no text layer — used to satisfy extract_pdf's
    is_scanned_pdf() call without needing real Tibetan content."""
    import fitz
    doc = fitz.open()
    doc.new_page(width=595, height=842)
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


# ---------------------------------------------------------------------------
# _has_broken_cmap: PUA detection
# ---------------------------------------------------------------------------

class TestPUADetection:

    def test_clean_tibetan_not_flagged(self):
        text = "བོད་ཡིག་གི་སྐད་ཡིག"
        assert not _has_broken_cmap(_pages(text))

    def test_empty_text_not_flagged(self):
        assert not _has_broken_cmap(_pages(""))

    def test_whitespace_only_not_flagged(self):
        assert not _has_broken_cmap(_pages("   \n\t  "))

    def test_below_threshold_not_flagged(self):
        # One PUA character among many non-PUA — well under 5%
        pua_char = "\uE001"
        text = "བོད་ཡིག་གི་སྐད་ཡིག" * 10 + pua_char
        assert not _has_broken_cmap(_pages(text))

    def test_above_threshold_flagged(self):
        # All PUA characters — 100%, well above 5%
        text = "\uE001\uE002\uE003\uE004\uE005" * 20
        assert _has_broken_cmap(_pages(text))

    def test_exactly_at_threshold_not_flagged(self):
        # Ratio == threshold is not strictly greater, should not trigger
        non_pua = "a" * 95
        pua = "\uE001" * 5  # exactly 5%
        assert not _has_broken_cmap(_pages(non_pua + pua))

    def test_just_above_threshold_flagged(self):
        non_pua = "a" * 94
        pua = "\uE001" * 6  # ~6%, above 5%
        assert _has_broken_cmap(_pages(non_pua + pua))

    def test_mixed_pages_accumulates_across_pages(self):
        # Spread PUA across multiple pages — should still detect
        pages = [
            PageContent(page_number=i + 1, text="\uE001" * 10 + "a" * 10)
            for i in range(5)
        ]
        assert _has_broken_cmap(pages)


# ---------------------------------------------------------------------------
# _has_broken_cmap: Himalaya vowel-O phantom detection
# ---------------------------------------------------------------------------

class TestHimalayaVowelPhantomDetection:

    def test_clean_tibetan_not_flagged(self):
        text = "བོད་ཡིག་གི་སྐད་ཡིག"
        assert not _has_broken_cmap(_pages(text))

    def test_below_threshold_not_flagged(self):
        # One or two occurrences could be legitimate (e.g. སྐྱོབས)
        text = "prefix" + _HIMALAYA_VOWEL_O_PHANTOM * (BROKEN_CMAP_HIMALAYA_VOWEL_THRESHOLD - 1)
        assert not _has_broken_cmap(_pages(text))

    def test_at_threshold_flagged(self):
        text = _HIMALAYA_VOWEL_O_PHANTOM * BROKEN_CMAP_HIMALAYA_VOWEL_THRESHOLD
        assert _has_broken_cmap(_pages(text))

    def test_well_above_threshold_flagged(self):
        # Simulates a real Himalaya document (hundreds of occurrences)
        text = _HIMALAYA_VOWEL_O_PHANTOM * 50
        assert _has_broken_cmap(_pages(text))

    def test_phantom_spread_across_pages_flagged(self):
        pages = [
            PageContent(page_number=i + 1, text=_HIMALAYA_VOWEL_O_PHANTOM * 2)
            for i in range(3)
        ]
        # 6 total > threshold of 3
        assert _has_broken_cmap(pages)

    def test_phantom_in_clean_tibetan_context_flagged(self):
        # Realistic: mostly clean text with the phantom injected
        clean = "བོད་ཡིག་གི་སྐད་ཡིག་" * 20
        corrupted = clean + _HIMALAYA_VOWEL_O_PHANTOM * BROKEN_CMAP_HIMALAYA_VOWEL_THRESHOLD
        assert _has_broken_cmap(_pages(corrupted))

    def test_older_himalaya_phantom_subjoined_tsa_flagged(self):
        # Older Word/OS versions insert subjoined TSA (U+0FA9) before vowel O
        older_phantom = _HIMALAYA_VOWEL_O_PHANTOMS[1]
        text = older_phantom * BROKEN_CMAP_HIMALAYA_VOWEL_THRESHOLD
        assert _has_broken_cmap(_pages(text))

    def test_all_known_phantoms_covered(self):
        # Every pattern in _HIMALAYA_VOWEL_O_PHANTOMS must trigger detection
        for phantom in _HIMALAYA_VOWEL_O_PHANTOMS:
            text = phantom * BROKEN_CMAP_HIMALAYA_VOWEL_THRESHOLD
            assert _has_broken_cmap(_pages(text)), f"Phantom not detected: {phantom!r}"


# ---------------------------------------------------------------------------
# _uses_broken_cmap_font: font-name detection
# ---------------------------------------------------------------------------

class TestFontNameDetection:

    def test_clean_pdf_not_flagged(self):
        # A PDF with no Himalaya font should not trigger font detection
        assert not _uses_broken_cmap_font(_minimal_pdf_bytes())

    def test_himalaya_pdf_flagged(self):
        PARITY_DIR = Path(__file__).parent / "fixtures" / "parity"
        pdf_path = PARITY_DIR / "Tashi Gyedpa.pdf"
        if not pdf_path.exists():
            pytest.skip("Tashi Gyedpa fixture not available")
        assert _uses_broken_cmap_font(pdf_path.read_bytes())

    def test_non_himalaya_tibetan_pdf_not_flagged(self):
        PARITY_DIR = Path(__file__).parent / "fixtures" / "parity"
        pdf_path = PARITY_DIR / "Tsongkhapa Prayer.pdf"
        if not pdf_path.exists():
            pytest.skip("Tsongkhapa Prayer fixture not available")
        assert not _uses_broken_cmap_font(pdf_path.read_bytes())


# ---------------------------------------------------------------------------
# extract_pdf routing: OCR fallback triggered when CMap is broken
# ---------------------------------------------------------------------------

class TestExtractPDFRouting:
    """
    Verify that extract_pdf routes to OCR (is_scanned=True) when _has_broken_cmap
    detects corruption, and stays on the digital path (is_scanned=False) for
    clean PDFs.

    extract_digital and extract_scanned are mocked so tests run without disk
    fixtures, real fonts, or the OCR engine.
    """

    def _dummy_pages(self, text: str) -> list[PageContent]:
        return [PageContent(page_number=1, text=text, width=595, height=842)]

    def test_clean_digital_pdf_uses_fitz(self):
        clean_text = "བོད་ཡིག་གི་སྐད་ཡིག"
        pdf_bytes = _minimal_pdf_bytes()

        with patch("app.pdf.extractor.extract_digital", return_value=self._dummy_pages(clean_text)) as mock_digital, \
             patch("app.pdf.extractor.extract_scanned") as mock_ocr, \
             patch("app.pdf.extractor.is_scanned_pdf", return_value=False), \
             patch("app.pdf.extractor._uses_broken_cmap_font", return_value=False):

            from app.pdf.extractor import extract_pdf
            pages, is_scanned = extract_pdf(pdf_bytes)

        assert not is_scanned
        mock_digital.assert_called_once()
        mock_ocr.assert_not_called()

    def test_himalaya_font_detected_routes_to_ocr_before_extraction(self):
        """Font-name detection should short-circuit before extract_digital is called."""
        ocr_text = "བོད་ཡིག་གི་སྐད་ཡིག"
        pdf_bytes = _minimal_pdf_bytes()

        with patch("app.pdf.extractor.is_scanned_pdf", return_value=False), \
             patch("app.pdf.extractor._uses_broken_cmap_font", return_value=True), \
             patch("app.pdf.extractor.extract_digital") as mock_digital, \
             patch("app.pdf.extractor.extract_scanned", return_value=self._dummy_pages(ocr_text)) as mock_ocr:

            from app.pdf.extractor import extract_pdf
            pages, is_scanned = extract_pdf(pdf_bytes)

        assert is_scanned
        mock_digital.assert_not_called()
        mock_ocr.assert_called_once()
        assert pages[0].text == ocr_text

    def test_himalaya_corrupted_text_falls_back_to_ocr(self):
        """Text-level backstop: CMap phantom detected after extraction."""
        corrupted_text = _HIMALAYA_VOWEL_O_PHANTOM * 50
        ocr_text = "བོད་ཡིག་གི་སྐད་ཡིག"
        pdf_bytes = _minimal_pdf_bytes()

        with patch("app.pdf.extractor.extract_digital", return_value=self._dummy_pages(corrupted_text)), \
             patch("app.pdf.extractor.extract_scanned", return_value=self._dummy_pages(ocr_text)) as mock_ocr, \
             patch("app.pdf.extractor.is_scanned_pdf", return_value=False), \
             patch("app.pdf.extractor._uses_broken_cmap_font", return_value=False):

            from app.pdf.extractor import extract_pdf
            pages, is_scanned = extract_pdf(pdf_bytes)

        assert is_scanned
        mock_ocr.assert_called_once()
        assert pages[0].text == ocr_text

    def test_pua_corrupted_pdf_falls_back_to_ocr(self):
        corrupted_text = "\uE001" * 100
        ocr_text = "བོད་ཡིག་གི་སྐད་ཡིག"
        pdf_bytes = _minimal_pdf_bytes()

        with patch("app.pdf.extractor.extract_digital", return_value=self._dummy_pages(corrupted_text)), \
             patch("app.pdf.extractor.extract_scanned", return_value=self._dummy_pages(ocr_text)) as mock_ocr, \
             patch("app.pdf.extractor.is_scanned_pdf", return_value=False), \
             patch("app.pdf.extractor._uses_broken_cmap_font", return_value=False):

            from app.pdf.extractor import extract_pdf
            pages, is_scanned = extract_pdf(pdf_bytes)

        assert is_scanned
        mock_ocr.assert_called_once()

    def test_image_only_pdf_goes_directly_to_ocr(self):
        """Scanned PDFs bypass fitz entirely — extract_digital should not be called."""
        ocr_text = "བོད་ཡིག་གི་སྐད་ཡིག"
        pdf_bytes = _minimal_pdf_bytes()

        with patch("app.pdf.extractor.is_scanned_pdf", return_value=True), \
             patch("app.pdf.extractor.extract_digital") as mock_digital, \
             patch("app.pdf.extractor.extract_scanned", return_value=self._dummy_pages(ocr_text)):

            from app.pdf.extractor import extract_pdf
            pages, is_scanned = extract_pdf(pdf_bytes)

        assert is_scanned
        mock_digital.assert_not_called()
