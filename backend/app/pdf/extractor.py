"""
PDF text extractor.

Two paths:
  - Digital PDFs (Unicode text embedded): pdfplumber extracts text + word positions.
  - Scanned PDFs (image-only): pdf2image renders pages → BDRC OCR runs → line positions.

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
    """
    import pdfplumber
    import io

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        sample_pages = pdf.pages[:3]
        total_chars = sum(len(p.extract_text() or "") for p in sample_pages)
        return total_chars < DIGITAL_TEXT_THRESHOLD * len(sample_pages)


def extract_digital(pdf_bytes: bytes) -> list[PageContent]:
    """Extract text and word positions from a digital PDF using pdfplumber."""
    import pdfplumber
    import io

    pages: list[PageContent] = []

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            raw_words = page.extract_words() or []

            words = [
                WordPosition(
                    text=w["text"],
                    x0=w["x0"],
                    y0=w["top"],
                    x1=w["x1"],
                    y1=w["bottom"],
                )
                for w in raw_words
            ]

            pages.append(
                PageContent(
                    page_number=i + 1,
                    text=text,
                    words=words,
                    is_scanned=False,
                    width=float(page.width),
                    height=float(page.height),
                )
            )

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
    pages: list[PageContent] = []

    for i, pil_img in enumerate(pil_pages):
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


# If more than this fraction of non-whitespace characters are outside the
# Tibetan Unicode block (U+0F00–U+0FFF), the PDF likely has a broken CMap
# (e.g. Microsoft Himalaya stacked glyphs with no ToUnicode entries).
BROKEN_CMAP_THRESHOLD = 0.05


def _has_broken_cmap(pages: list[PageContent]) -> bool:
    """
    Heuristic: scan extracted text for non-Tibetan, non-whitespace characters.

    Some Word-generated PDFs use fonts (e.g. Microsoft Himalaya) whose ToUnicode
    CMap covers only base consonants, leaving stacked glyphs unmapped. Both
    pdfplumber and PyMuPDF fall back to raw glyph byte values for unmapped
    glyphs, which land in the ASCII range. A high ratio of such characters
    signals that pdfplumber extraction is unreliable for this PDF.
    """
    total = 0
    non_tibetan = 0
    for page in pages:
        for ch in page.text:
            if ch.isspace():
                continue
            total += 1
            if not (0x0F00 <= ord(ch) <= 0x0FFF):
                non_tibetan += 1
    if total == 0:
        return False
    ratio = non_tibetan / total
    if ratio > BROKEN_CMAP_THRESHOLD:
        logger.warning(
            "Broken CMap suspected: %.1f%% non-Tibetan chars in extracted text "
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

    logger.info("PDF detected as digital — using pdfplumber text extraction")
    pages = extract_digital(pdf_bytes)

    if _has_broken_cmap(pages):
        logger.info("Broken CMap detected — re-routing digital PDF through BDRC OCR")
        return extract_scanned(pdf_bytes), True

    return pages, False
