"""
.docx exporter.

Converts extracted page content into an editable Word document with spell errors
marked up (red underline + yellow highlight). This is the translator-facing output:
open in Word or LibreOffice, edit inline, add translation notes.

Future: two-column layout (Tibetan | translation space), definition sidebars.
"""
import io
import logging
from typing import Any

from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_COLOR_INDEX

logger = logging.getLogger(__name__)


def build_docx(
    pages: list[Any],              # list[PageContent]
    errors_by_page: dict[int, list[str]],  # page_number → list of error words
    filename: str = "document",
) -> bytes:
    """
    Build a .docx from extracted page content.

    Each page becomes a section. Words matching error_words are marked with
    a red underline and yellow highlight so they stand out for the translator.

    Returns the .docx as bytes.
    """
    doc = Document()

    # Document title
    doc.add_heading(f"OCR Output — {filename}", level=1)

    for page_content in pages:
        error_words = set(errors_by_page.get(page_content.page_number, []))

        # Page heading
        doc.add_heading(f"Page {page_content.page_number}", level=2)

        if not page_content.text.strip():
            doc.add_paragraph("[No text detected on this page]")
            continue

        # Process the page text line by line, then word by word
        for line in page_content.text.splitlines():
            if not line.strip():
                doc.add_paragraph("")
                continue

            para = doc.add_paragraph()
            _add_line_with_errors(para, line, error_words)

        # Page break between pages (except after the last page)
        if page_content.page_number < len(pages):
            doc.add_page_break()

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _add_line_with_errors(para: Any, line: str, error_words: set[str]) -> None:
    """
    Split a line into tokens and add each as a run.
    Error words get red underline + yellow highlight.
    """
    # Tibetan text is syllable-delimited by ་ (tsheg, U+0F0B) and spaces.
    # We split on spaces to get rough tokens for markup.
    # The spell checker works at syllable level; errors are reported as syllables.
    tokens = line.split(" ")

    for i, token in enumerate(tokens):
        if not token:
            if i < len(tokens) - 1:
                para.add_run(" ")
            continue

        # Check if this token (or any tsheg-delimited syllable within it) is an error
        is_error = token in error_words or any(
            syl in error_words for syl in token.split("\u0F0B") if syl
        )

        run = para.add_run(token)
        run.font.size = Pt(14)  # Tibetan script needs a larger size to be readable

        if is_error:
            run.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)  # dark red
            run.font.underline = True
            _set_highlight(run, WD_COLOR_INDEX.YELLOW)

        # Space between tokens
        if i < len(tokens) - 1:
            para.add_run(" ")


def _set_highlight(run: Any, color: Any) -> None:
    """Apply a highlight color to a run via direct XML (python-docx doesn't expose this cleanly)."""
    rPr = run._r.get_or_add_rPr()
    highlight = OxmlElement("w:highlight")
    highlight.set(qn("w:val"), "yellow")
    rPr.append(highlight)
