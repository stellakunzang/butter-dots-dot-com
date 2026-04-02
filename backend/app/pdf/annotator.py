"""
PDF annotator.

Takes the original PDF bytes + structured spell errors and produces an annotated
PDF with error syllables highlighted in yellow. Uses PyMuPDF (fitz) for annotation.

For digital PDFs: fitz.search_for() locates each error syllable's exact position
directly from the PDF's text layer, bypassing the pdfplumber word-cluster mismatch.

For scanned PDFs: OCR line bboxes are the only positional data available
(syllable-level coordinates require per-glyph OCR, which BDRC's pipeline doesn't
expose). We highlight any OCR line that contains at least one error syllable.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Highlight color: yellow
HIGHLIGHT_COLOR = (1.0, 0.95, 0.0)  # RGB, fitz uses 0.0–1.0


def annotate_pdf(
    pdf_bytes: bytes,
    pages: list[Any],   # list[PageContent]
    errors_by_page: dict[int, list[str]],  # page_number → list of error syllables
) -> bytes:
    """
    Add yellow highlight annotations to error syllables in the PDF.

    For digital PDFs: searches the text layer for each error syllable and
    highlights its exact bounding rect.
    For scanned PDFs: highlights any OCR line bbox that contains an error syllable.

    Args:
        pdf_bytes: Original PDF file bytes
        pages: PageContent list from extractor
        errors_by_page: Dict mapping 1-based page numbers to lists of error syllables

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
            _annotate_digital_page(fitz_page, error_set)

    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


def _annotate_digital_page(fitz_page: Any, error_set: set[str]) -> None:
    """
    For digital PDFs, use fitz.search_for() to locate each error syllable
    in the PDF's text layer directly.

    This bypasses the pdfplumber word-cluster mismatch: pdfplumber groups
    multiple syllables into a single 'word' separated by whitespace, so
    individual syllable strings never matched the word-box text. fitz.search_for
    does a substring search on the rendered text and returns exact quads.
    """
    import fitz

    highlighted: set[str] = set()
    for syllable in error_set:
        if not syllable:
            continue
        # search_for returns a list of Rect matching the text positions
        rects = fitz_page.search_for(syllable)
        if not rects:
            logger.debug("Syllable %r not found in PDF text layer (page %d)", syllable, fitz_page.number + 1)
            continue
        for rect in rects:
            annot = fitz_page.add_highlight_annot(rect)
            annot.set_colors(stroke=HIGHLIGHT_COLOR)
            annot.update()
        highlighted.add(syllable)

    if highlighted:
        logger.debug("Highlighted %d error syllable(s) on page %d", len(highlighted), fitz_page.number + 1)


def _annotate_scanned_page(fitz_page: Any, page_content: Any, error_set: set[str]) -> None:
    """
    For scanned PDFs, positions are OCR line bboxes in image pixel space (300 DPI).
    We highlight entire lines that contain at least one error syllable.

    Per-syllable granularity would require glyph-level coordinates from the OCR
    pipeline, which BDRC does not currently expose.
    """
    import fitz

    OCR_DPI = 300
    scale = 72.0 / OCR_DPI

    pdf_w = fitz_page.rect.width
    pdf_h = fitz_page.rect.height

    for word_pos in page_content.words:
        # word_pos.text is the full OCR line; check if any error syllable appears in it
        line_syllables = {syl for syl in word_pos.text.split("\u0F0B") if syl}
        if not (line_syllables & error_set):
            continue

        # Scale pixel coords → PDF points
        x0 = max(0.0, min(word_pos.x0 * scale, pdf_w))
        y0 = max(0.0, min(word_pos.y0 * scale, pdf_h))
        x1 = max(0.0, min(word_pos.x1 * scale, pdf_w))
        y1 = max(0.0, min(word_pos.y1 * scale, pdf_h))

        if x1 > x0 and y1 > y0:
            rect = fitz.Rect(x0, y0, x1, y1)
            annot = fitz_page.add_highlight_annot(rect)
            annot.set_colors(stroke=HIGHLIGHT_COLOR)
            annot.update()
