"""
PDF annotator.

Takes the original PDF bytes + structured spell errors and produces an annotated
PDF with error words highlighted in yellow. Uses PyMuPDF (fitz) for annotation.

For digital PDFs, word positions come from pdfplumber (precise).
For scanned PDFs, positions are line-level bounding boxes from BDRC OCR.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Highlight color: yellow with some transparency
HIGHLIGHT_COLOR = (1.0, 0.95, 0.0)  # RGB, fitz uses 0.0–1.0


def annotate_pdf(
    pdf_bytes: bytes,
    pages: list[Any],   # list[PageContent]
    errors_by_page: dict[int, list[str]],  # page_number → list of error words
) -> bytes:
    """
    Add yellow highlight annotations to error words in the PDF.

    For digital PDFs: highlights the exact word bounding box from pdfplumber.
    For scanned PDFs: highlights the line bounding box containing the error.

    Args:
        pdf_bytes: Original PDF file bytes
        pages: PageContent list from extractor
        errors_by_page: Dict mapping 1-based page numbers to lists of error words

    Returns:
        Annotated PDF bytes
    """
    import fitz  # PyMuPDF
    import io

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    for page_content in pages:
        page_num = page_content.page_number  # 1-based
        error_words = errors_by_page.get(page_num, [])

        if not error_words:
            continue

        error_set = set(error_words)
        fitz_page = doc[page_num - 1]  # fitz uses 0-based

        if page_content.is_scanned:
            _annotate_scanned_page(fitz_page, page_content, error_set)
        else:
            _annotate_digital_page(fitz_page, page_content, error_set)

    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


def _annotate_digital_page(fitz_page: Any, page_content: Any, error_set: set[str]) -> None:
    """Highlight individual words by their exact PDF coordinates."""
    import fitz

    pdf_w = fitz_page.rect.width
    pdf_h = fitz_page.rect.height

    for word_pos in page_content.words:
        if word_pos.text in error_set:
            x0 = max(0.0, min(word_pos.x0, pdf_w))
            y0 = max(0.0, min(word_pos.y0, pdf_h))
            x1 = max(0.0, min(word_pos.x1, pdf_w))
            y1 = max(0.0, min(word_pos.y1, pdf_h))

            if x1 > x0 and y1 > y0:
                rect = fitz.Rect(x0, y0, x1, y1)
                annot = fitz_page.add_highlight_annot(rect)
                annot.set_colors(stroke=HIGHLIGHT_COLOR)
                annot.update()


def _annotate_scanned_page(fitz_page: Any, page_content: Any, error_set: set[str]) -> None:
    """
    For scanned PDFs, positions are in image pixel space (at 300 DPI).
    We need to scale from image pixels to PDF points.

    PDF points = image pixels * (72 / DPI)
    """
    import fitz

    OCR_DPI = 300
    scale = 72.0 / OCR_DPI

    pdf_w = fitz_page.rect.width
    pdf_h = fitz_page.rect.height

    for word_pos in page_content.words:
        if word_pos.text in error_set:
            # Scale pixel coords → PDF points
            x0 = word_pos.x0 * scale
            y0 = word_pos.y0 * scale
            x1 = word_pos.x1 * scale
            y1 = word_pos.y1 * scale

            # Clamp to page bounds
            x0 = max(0.0, min(x0, pdf_w))
            y0 = max(0.0, min(y0, pdf_h))
            x1 = max(0.0, min(x1, pdf_w))
            y1 = max(0.0, min(y1, pdf_h))

            if x1 > x0 and y1 > y0:
                rect = fitz.Rect(x0, y0, x1, y1)
                annot = fitz_page.add_highlight_annot(rect)
                annot.set_colors(stroke=HIGHLIGHT_COLOR)
                annot.update()
