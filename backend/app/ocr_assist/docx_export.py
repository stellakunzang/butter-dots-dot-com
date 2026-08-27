"""
Clean DOCX export for the interactive OCR job store.

Mirrors ``tibetan-ocr-app`` ``DocxExporter``: each finalized page becomes a
``Page N`` Heading 2 section with Tibetan Machine Uni 14pt body text. No
spellcheck highlighting (that stays in ``app.pdf.docx_exporter``).

The file is rebuilt from disk on every finalize/reset so a crash mid-job
never duplicates pages and never leaves stale sections for reset pages.
"""
from __future__ import annotations

import io
import logging
import os
import tempfile
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Pt

from app.ocr_assist.job_store import OUTPUT_DOCX_FILE, Job, iter_finalized_pages

logger = logging.getLogger(__name__)

TIBETAN_FONT = "Tibetan Machine Uni"
BODY_FONT_PT = 14
HEADING_FONT_PT = 11


def build_clean_docx(pages: list[tuple[int, str]]) -> bytes:
    """Build a clean .docx from ``(page_index, text)`` pairs.

    Empty finalized text still gets a ``Page N`` heading and a placeholder
    paragraph so page numbering stays aligned with the source PDF.
    """
    doc = Document()
    for page_index, text in pages:
        heading = doc.add_heading(f"Page {page_index}", level=2)
        for run in heading.runs:
            run.font.size = Pt(HEADING_FONT_PT)

        body = text if text.strip() else "[No text on this page]"
        for line in body.splitlines() or [""]:
            para = doc.add_paragraph()
            run = para.add_run(line)
            _apply_tibetan_font(run, size_pt=BODY_FONT_PT)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def write_clean_docx(job: Job) -> Path | None:
    """Write (or remove) ``jobs/<id>/output.docx`` from finalized pages.

    Returns the path when at least one page is finalized; otherwise deletes
    any stale ``output.docx`` and returns ``None``.
    """
    out_path = job.root / OUTPUT_DOCX_FILE
    pages = iter_finalized_pages(job)
    if not pages:
        out_path.unlink(missing_ok=True)
        return None

    payload = build_clean_docx(pages)
    _atomic_write_bytes(out_path, payload)
    logger.info(
        "wrote %s (%d finalized page(s))",
        out_path.resolve(),
        len(pages),
    )
    return out_path


def _apply_tibetan_font(run, *, size_pt: int) -> None:
    run.font.name = TIBETAN_FONT
    run.font.size = Pt(size_pt)
    # Word uses eastAsia for Tibetan; setting ascii name alone is not enough
    # on all platforms.
    r_pr = run._element.get_or_add_rPr()
    r_fonts = r_pr.get_or_add_rFonts()
    r_fonts.set(qn("w:ascii"), TIBETAN_FONT)
    r_fonts.set(qn("w:hAnsi"), TIBETAN_FONT)
    r_fonts.set(qn("w:eastAsia"), TIBETAN_FONT)


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    """Write ``content`` to ``path`` atomically (temp + replace + fsync)."""
    fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=path.name + ".", suffix=".tmp"
    )
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise

    try:
        dir_fd = os.open(str(path.parent), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(dir_fd)
    except OSError:
        pass
    finally:
        os.close(dir_fd)
