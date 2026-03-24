"""
Tests for the PDF annotator.

Uses synthetic PDFs built with ReportLab (or fitz directly) to verify that:
  - Digital PDFs: error syllables are located and highlighted via search_for
  - Scanned PDFs: OCR lines containing error syllables get line-level highlights
  - No crashes on empty error sets
"""
import io
import pytest


def _make_digital_pdf(text: str) -> bytes:
    """
    Create a minimal single-page digital PDF with searchable text.

    Uses fitz with the built-in Helvetica font (Latin characters only).
    The digital-annotator tests use ASCII error tokens to avoid font support
    issues — the search_for mechanism is encoding-agnostic.
    """
    import fitz
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4
    page.insert_text((50, 100), text, fontsize=12)
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


def _count_highlights(pdf_bytes: bytes) -> int:
    """Count the number of highlight annotations across all pages."""
    import fitz
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    count = 0
    for page in doc:
        count += sum(1 for a in page.annots() if a.type[0] == 8)  # 8 = Highlight
    doc.close()
    return count


class TestAnnotateDigitalPage:
    """
    Uses ASCII text in a Helvetica-font PDF to test the search_for mechanism.
    The logic is encoding-agnostic: Tibetan syllables work identically to ASCII
    tokens as long as the PDF has a searchable text layer.
    """

    def test_error_token_gets_highlighted(self):
        """search_for should find the error token and create a highlight."""
        from app.pdf.extractor import PageContent
        from app.pdf.annotator import annotate_pdf

        text = "hello ERROR world"
        pdf_bytes = _make_digital_pdf(text)

        page = PageContent(page_number=1, text=text, is_scanned=False)
        errors_by_page = {1: ["ERROR"]}

        result = annotate_pdf(pdf_bytes, [page], errors_by_page)
        assert _count_highlights(result) >= 1

    def test_no_highlights_when_no_errors(self):
        """Clean text with no errors should produce zero highlight annotations."""
        from app.pdf.extractor import PageContent
        from app.pdf.annotator import annotate_pdf

        text = "hello world"
        pdf_bytes = _make_digital_pdf(text)

        page = PageContent(page_number=1, text=text, is_scanned=False)
        result = annotate_pdf(pdf_bytes, [page], {})
        assert _count_highlights(result) == 0

    def test_no_highlights_when_error_not_in_text(self):
        """An error token absent from the page should not produce annotations."""
        from app.pdf.extractor import PageContent
        from app.pdf.annotator import annotate_pdf

        text = "hello world"
        pdf_bytes = _make_digital_pdf(text)

        page = PageContent(page_number=1, text=text, is_scanned=False)
        errors_by_page = {1: ["MISSING"]}  # not present in text

        result = annotate_pdf(pdf_bytes, [page], errors_by_page)
        assert _count_highlights(result) == 0

    def test_returns_valid_pdf_bytes(self):
        """annotate_pdf should always return openable PDF bytes."""
        import fitz
        from app.pdf.extractor import PageContent
        from app.pdf.annotator import annotate_pdf

        text = "hello ERROR world"
        pdf_bytes = _make_digital_pdf(text)
        page = PageContent(page_number=1, text=text, is_scanned=False)
        result = annotate_pdf(pdf_bytes, [page], {1: ["ERROR"]})

        doc = fitz.open(stream=result, filetype="pdf")
        assert doc.page_count == 1
        doc.close()


class TestAnnotateScannedPage:

    def _make_scanned_page_content(self, lines: list[str], dpi: int = 300):
        """Construct a mock PageContent with OCR-style line bboxes."""
        from app.pdf.extractor import PageContent, WordPosition
        words = []
        y = 0
        for line_text in lines:
            words.append(WordPosition(
                text=line_text,
                x0=0, y0=y, x1=500, y1=y + 50
            ))
            y += 60

        text = "\n".join(lines)
        return PageContent(
            page_number=1, text=text, words=words, is_scanned=True,
            width=500, height=y + 60,
        )

    def _make_blank_pdf(self) -> bytes:
        import fitz
        doc = fitz.open()
        doc.new_page(width=595, height=842)
        buf = io.BytesIO()
        doc.save(buf)
        doc.close()
        return buf.getvalue()

    def test_line_containing_error_gets_highlighted(self):
        from app.pdf.annotator import annotate_pdf
        page_content = self._make_scanned_page_content([
            "རིན་པོ་ཆེར་གཀར་གྱི་",
            "བོད་ཡིག་གི་སྐད་",
        ])
        pdf_bytes = self._make_blank_pdf()
        result = annotate_pdf(pdf_bytes, [page_content], {1: ["གཀར"]})
        # Only the first line contains གཀར — expect exactly 1 highlight
        assert _count_highlights(result) == 1

    def test_line_without_error_not_highlighted(self):
        from app.pdf.annotator import annotate_pdf
        page_content = self._make_scanned_page_content([
            "བོད་ཡིག་གི་སྐད་",
        ])
        pdf_bytes = self._make_blank_pdf()
        result = annotate_pdf(pdf_bytes, [page_content], {1: ["གཀར"]})
        assert _count_highlights(result) == 0

    def test_multiple_lines_with_errors_all_highlighted(self):
        from app.pdf.annotator import annotate_pdf
        page_content = self._make_scanned_page_content([
            "གཀར་ཡིག",
            "བོད་གཀར་",
            "ཡིག་གི་",  # no error
        ])
        pdf_bytes = self._make_blank_pdf()
        result = annotate_pdf(pdf_bytes, [page_content], {1: ["གཀར"]})
        assert _count_highlights(result) == 2
