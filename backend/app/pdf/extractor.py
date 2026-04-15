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


BROKEN_CMAP_PUA_THRESHOLD = 0.05
BROKEN_CMAP_HIMALAYA_VOWEL_THRESHOLD = 3

# Microsoft Himalaya's CMap maps the vowel sign O (U+0F7C) glyph back to a
# phantom subjoined consonant sequence that varies by Word/OS version:
#   - Newer versions: U+0F90 U+0FB1 U+0F7C (subjoined KA + subjoined YA + vowel O)
#   - Older versions: U+0FA9 U+0F7C (subjoined TSA + vowel O)
# Font-name detection (see _uses_himalaya_font) is the primary check; these
# phantom patterns are kept as a backstop for cases where the font name is
# embedded differently or stripped by the PDF producer.
_HIMALAYA_VOWEL_O_PHANTOMS = [
    "\u0F90\u0FB1\u0F7C",  # subjoined KA + subjoined YA + vowel O
    "\u0FA9\u0F7C",         # subjoined TSA + vowel O
]

# Convenience export used by tests.
_HIMALAYA_VOWEL_O_PHANTOM = _HIMALAYA_VOWEL_O_PHANTOMS[0]

# Font names that are known to produce broken CMap output with fitz.
_BROKEN_CMAP_FONTS = {"MicrosoftHimalaya"}


def _uses_broken_cmap_font(pdf_bytes: bytes) -> bool:
    """
    Return True if the PDF embeds any font known to produce broken CMap output.

    Microsoft Himalaya is the primary offender: different Word/OS versions map
    the Tibetan vowel sign ོ to different phantom subjoined-consonant sequences,
    all of which produce cascading false-positive spelling errors. Detecting the
    font name before extraction is more reliable than pattern-matching the
    extracted text, because the phantom sequence varies between versions.
    """
    import fitz

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        for page in doc:
            for block in page.get_text("rawdict").get("blocks", []):
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        if span.get("font", "") in _BROKEN_CMAP_FONTS:
                            logger.warning(
                                "Broken CMap font detected: %r — falling back to OCR",
                                span["font"],
                            )
                            return True
    finally:
        doc.close()
    return False


def _has_broken_cmap(pages: list[PageContent]) -> bool:
    """
    Detect broken ToUnicode CMap tables in fitz-extracted Tibetan text.

    Used as a backstop after font-name detection (_uses_broken_cmap_font) for
    fonts whose name may be stripped or embedded differently by the PDF producer.

    Two text-level heuristics:

    1. **PUA codepoints** — When a font's CMap is absent or incomplete, fitz
       returns raw glyph IDs that land in the Private Use Area (U+E000–U+F8FF).
       If more than 5% of non-whitespace characters are PUA, the CMap is broken.

    2. **Himalaya vowel-O phantoms** — Microsoft Himalaya maps the vowel sign ོ
       (U+0F7C) to a phantom subjoined-consonant sequence before it. Three or
       more occurrences of any known phantom pattern trigger the fallback.
    """
    total = 0
    pua = 0
    full_text = ""
    for page in pages:
        full_text += page.text
        for ch in page.text:
            if ch.isspace():
                continue
            total += 1
            if 0xE000 <= ord(ch) <= 0xF8FF:
                pua += 1

    if total == 0:
        return False

    pua_ratio = pua / total
    logger.info(
        "CMap check: %.1f%% PUA chars out of %d total (threshold %.1f%%)",
        pua_ratio * 100,
        total,
        BROKEN_CMAP_PUA_THRESHOLD * 100,
    )
    if pua_ratio > BROKEN_CMAP_PUA_THRESHOLD:
        logger.warning(
            "Broken CMap suspected: %.1f%% PUA codepoints (threshold %.1f%%) "
            "— falling back to OCR",
            pua_ratio * 100,
            BROKEN_CMAP_PUA_THRESHOLD * 100,
        )
        return True

    for phantom in _HIMALAYA_VOWEL_O_PHANTOMS:
        count = full_text.count(phantom)
        if count >= BROKEN_CMAP_HIMALAYA_VOWEL_THRESHOLD:
            logger.warning(
                "Broken CMap suspected: Himalaya vowel-O phantom %r found %d "
                "times (threshold %d) — falling back to OCR",
                phantom,
                count,
                BROKEN_CMAP_HIMALAYA_VOWEL_THRESHOLD,
            )
            return True

    return False


def extract_pdf(pdf_bytes: bytes) -> tuple[list[PageContent], bool]:
    """
    Main entry point. Detects PDF type and routes accordingly.

    For digital PDFs, checks for broken font CMap encoding in two passes:
      1. Font-name check — known offenders (e.g. MicrosoftHimalaya) are routed
         to OCR immediately, before any text is extracted.
      2. Text-level check — PUA codepoints and known phantom sequences catch
         corrupt fonts whose names are stripped or embedded differently.

    Returns:
        (pages, is_scanned) tuple
    """
    scanned = is_scanned_pdf(pdf_bytes)

    if scanned:
        logger.info("PDF detected as scanned — using BDRC OCR pipeline")
        return extract_scanned(pdf_bytes), True

    logger.info("PDF detected as digital — using fitz text extraction")

    if _uses_broken_cmap_font(pdf_bytes):
        logger.info("Broken CMap font detected — routing digital PDF through BDRC OCR")
        return extract_scanned(pdf_bytes), True

    pages = extract_digital(pdf_bytes)

    if _has_broken_cmap(pages):
        logger.info("Broken CMap detected in extracted text — re-routing through BDRC OCR")
        return extract_scanned(pdf_bytes), True

    return pages, False
