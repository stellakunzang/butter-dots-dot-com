"""
PDF text extractor.

Two paths:
  - Digital PDFs (Unicode text embedded): fitz (PyMuPDF) extracts text + word positions.
    If the extracted text contains a high ratio of Private Use Area characters (a sign
    of a broken ToUnicode CMap, common in MS Himalaya and some older Tibetan fonts),
    the pipeline falls back to the OCR path.
  - Scanned PDFs (image-only): pdf2image renders pages → BDRC OCR runs → line positions.

fitz is used throughout the digital path instead of pdfplumber because fitz handles
Tibetan font ToUnicode CMap tables more reliably — in particular, fonts like Jomolhari
that pdfplumber cannot decode correctly.

Returns a list of PageContent objects that the rest of the pipeline operates on,
regardless of which path was taken.
"""
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Minimum number of characters to consider a page "digital" (has embedded text)
DIGITAL_TEXT_THRESHOLD = 10


@dataclass
class WordPosition:
    """A word and its bounding box on a page (in PDF points for digital, pixels for scanned)."""
    text: str
    x0: float
    y0: float
    x1: float
    y1: float


@dataclass
class PageContent:
    """Extracted content for a single page."""
    page_number: int  # 1-based
    text: str         # Full page text, newline-separated lines
    words: list[WordPosition] = field(default_factory=list)
    is_scanned: bool = False
    # Original page dimensions (PDF points or pixels)
    width: float = 0.0
    height: float = 0.0


def is_scanned_pdf(pdf_bytes: bytes) -> bool:
    """
    Heuristic: if the first few pages have almost no embedded text, treat as scanned.
    Uses fitz for consistency with extract_digital().
    """
    import fitz

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    sample_pages = [doc[i] for i in range(min(3, len(doc)))]
    total_chars = sum(len(page.get_text()) for page in sample_pages)
    doc.close()
    return total_chars < DIGITAL_TEXT_THRESHOLD * max(len(sample_pages), 1)


def extract_digital(pdf_bytes: bytes) -> list[PageContent]:
    """
    Extract text and word positions from a digital PDF using fitz (PyMuPDF).

    fitz is preferred over pdfplumber for Tibetan PDFs because it correctly
    resolves ToUnicode CMap entries for fonts like Jomolhari that pdfplumber
    fails to decode, returning PUA garbage instead of proper Unicode.

    Word positions come from fitz's 'words' extraction mode, which returns
    whitespace-delimited token bboxes in PDF points — suitable for
    annotator.py's search_for() approach.
    """
    import fitz

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages: list[PageContent] = []

    for i, page in enumerate(doc):
        text = page.get_text("text")

        # fitz 'words' returns (x0, y0, x1, y1, word, block_no, line_no, word_no)
        raw_words = page.get_text("words")
        words = [
            WordPosition(
                text=w[4],
                x0=w[0],
                y0=w[1],
                x1=w[2],
                y1=w[3],
            )
            for w in raw_words
            if w[4].strip()
        ]

        pages.append(
            PageContent(
                page_number=i + 1,
                text=text,
                words=words,
                is_scanned=False,
                width=float(page.rect.width),
                height=float(page.rect.height),
            )
        )

    doc.close()
    return pages


def extract_scanned(pdf_bytes: bytes) -> list[PageContent]:
    """
    Convert each PDF page to an image, run BDRC OCR, return PageContent with
    line-level text and bounding boxes.
    """
    import io
    import cv2
    import numpy as np
    from pdf2image import convert_from_bytes
    from app.pdf.ocr import get_engine, OCRLine

    engine = get_engine()
    if not engine.ready:
        raise RuntimeError(f"OCR engine unavailable: {engine.error}")

    pil_pages = convert_from_bytes(pdf_bytes, dpi=300)
    total_pages = len(pil_pages)
    pages: list[PageContent] = []

    for i, pil_img in enumerate(pil_pages):
        logger.info("OCR: processing page %d of %d", i + 1, total_pages)
        # Convert PIL → BGR numpy array for BDRC pipeline
        img_rgb = np.array(pil_img)
        img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

        ocr_lines = engine.run_on_image(img_bgr)

        # Combine line texts into page text
        text = "\n".join(line.text for line in ocr_lines if line.text)

        # OCR lines as word-level approximations (line bbox, full line text)
        # Per-word segmentation within lines is a future improvement.
        words = [
            WordPosition(
                text=line.text,
                x0=float(line.x),
                y0=float(line.y),
                x1=float(line.x + line.width),
                y1=float(line.y + line.height),
            )
            for line in ocr_lines
            if line.text
        ]

        pages.append(
            PageContent(
                page_number=i + 1,
                text=text,
                words=words,
                is_scanned=True,
                width=float(pil_img.width),
                height=float(pil_img.height),
            )
        )

    return pages


# If more than this fraction of non-whitespace characters are Private Use Area
# codepoints (U+E000–U+F8FF), the PDF has a broken ToUnicode CMap.
# PUA characters appear when a font's CMap doesn't cover a glyph and the PDF
# renderer falls back to raw glyph IDs, which land in the PUA for many Tibetan
# fonts (e.g. Microsoft Himalaya stacked consonants).
#
# Deliberately NOT checking for "non-Tibetan" characters: mixed Tibetan/English
# documents legitimately contain ASCII, and flagging that as broken would send
# all mixed-script PDFs through OCR unnecessarily.
BROKEN_CMAP_THRESHOLD = 0.05


def _has_broken_cmap(pages: list[PageContent]) -> bool:
    """
    Heuristic: scan fitz-extracted text for Private Use Area (PUA) codepoints.

    When a font's ToUnicode CMap is absent or incomplete (common with MS Himalaya
    stacked glyphs), fitz returns raw glyph IDs instead of mapped Unicode. For
    Tibetan fonts these typically land in U+E000–U+F8FF (the PUA).

    ASCII printable characters are not counted as suspicious because documents
    can legitimately mix Tibetan and English/Latin script.
    """
    total = 0
    pua = 0
    for page in pages:
        for ch in page.text:
            if ch.isspace():
                continue
            total += 1
            cp = ord(ch)
            if 0xE000 <= cp <= 0xF8FF:
                pua += 1
    if total == 0:
        return False
    ratio = pua / total
    logger.info(
        "CMap check: %.1f%% PUA chars out of %d total (threshold %.1f%%)",
        ratio * 100,
        total,
        BROKEN_CMAP_THRESHOLD * 100,
    )
    if ratio > BROKEN_CMAP_THRESHOLD:
        logger.warning(
            "Broken CMap suspected: %.1f%% PUA codepoints in fitz-extracted text "
            "(threshold %.1f%%) — falling back to OCR",
            ratio * 100,
            BROKEN_CMAP_THRESHOLD * 100,
        )
        return True
    return False


def extract_pdf(pdf_bytes: bytes) -> tuple[list[PageContent], bool]:
    """
    Main entry point. Detects PDF type and routes accordingly.

    For digital PDFs, also checks for broken font CMap encoding (common with
    Microsoft Himalaya and similar Tibetan fonts generated from Word). If
    detected, falls back to the OCR path for accurate text extraction.

    Returns:
        (pages, is_scanned) tuple
    """
    scanned = is_scanned_pdf(pdf_bytes)

    if scanned:
        logger.info("PDF detected as scanned — using BDRC OCR pipeline")
        return extract_scanned(pdf_bytes), True

    logger.info("PDF detected as digital — using fitz text extraction")
    pages = extract_digital(pdf_bytes)

    if _has_broken_cmap(pages):
        logger.info("Broken CMap detected — re-routing digital PDF through BDRC OCR")
        return extract_scanned(pdf_bytes), True

    return pages, False
