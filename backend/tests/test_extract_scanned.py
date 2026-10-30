"""Scanned extraction: native-image path plus per-page render fallback."""

import cv2
import fitz
import numpy as np
from PIL import Image

from app.pdf.extractor import _native_scan_image, extract_scanned


def _page_with_embedded_image(
    img_w: int,
    img_h: int,
    *,
    page_w: float = 612.0,
    page_h: float = 792.0,
    add_text: bool = False,
    rotation: int = 0,
) -> fitz.Page:
    """A one-page PDF whose single image sits small on a larger page.

    Mirrors the real bug: a wide pecha strip dropped into a US-Letter page.
    """
    img = np.full((img_h, img_w, 3), 255, np.uint8)
    cv2.rectangle(img, (5, 5), (img_w - 5, img_h - 5), (0, 0, 0), 3)
    png = cv2.imencode(".png", img)[1].tobytes()

    doc = fitz.open()
    page = doc.new_page(width=page_w, height=page_h)
    # Place the image as a thin band, not filling the page.
    page.insert_image(fitz.Rect(40, 300, page_w - 40, 460), stream=png)
    if add_text:
        page.insert_text((40, 60), "digital text here")
    if rotation:
        page.set_rotation(rotation)
    return page


class TestNativeScanImage:
    def test_returns_image_at_native_resolution(self):
        """The embedded image is read at its own pixels, not the shrunk render."""
        page = _page_with_embedded_image(1200, 600)
        arr = _native_scan_image(page.parent, page)
        assert arr is not None
        assert arr.shape[:2] == (600, 1200)

    def test_skips_pages_with_extractable_text(self):
        """Text-bearing pages (incl. broken-CMap digital) use the render path."""
        page = _page_with_embedded_image(1200, 600, add_text=True)
        assert _native_scan_image(page.parent, page) is None

    def test_rejects_tiny_images(self):
        """Degenerate small images fall back to rendering."""
        page = _page_with_embedded_image(100, 40)
        assert _native_scan_image(page.parent, page) is None

    def test_honours_page_rotation(self):
        """A /Rotate 90 page yields an upright (transposed) native image."""
        page = _page_with_embedded_image(1000, 600, rotation=90)
        arr = _native_scan_image(page.parent, page)
        assert arr is not None
        # 90° rotation swaps the axes.
        assert arr.shape[:2] == (1000, 600)


class _RecordingEngine:
    ready = True
    error = None

    def __init__(self):
        self.seen_shapes: list[tuple[int, int]] = []

    def run_on_image(self, image):
        self.seen_shapes.append(image.shape[:2])

        class Line:
            text = "བོད"
            x = y = 0
            width = height = 1

        return [Line()]


def test_extract_scanned_prefers_native_image_over_render(monkeypatch):
    """The band-placed scan is OCR'd at native resolution, bypassing the render.

    This is the regression guard for the letter-page-wrapping bug: rendering the
    612x792 page at 300 DPI would hand OCR a ~2550x3300 canvas with the scan
    shrunk to a band; the native path hands it the full 1000x400 image instead.
    """
    page = _page_with_embedded_image(1200, 600)
    pdf_bytes = page.parent.tobytes()

    engine = _RecordingEngine()
    convert_calls: list = []

    def fail_convert(*_args, **_kwargs):
        convert_calls.append(_kwargs)
        raise AssertionError("native path should not render this page")

    monkeypatch.setattr("app.pdf.ocr.get_engine", lambda: engine)
    monkeypatch.setattr("pdf2image.convert_from_bytes", fail_convert)

    pages = extract_scanned(pdf_bytes)

    assert convert_calls == []
    assert engine.seen_shapes == [(600, 1200)]
    assert pages[0].is_scanned is True
    assert (int(pages[0].width), int(pages[0].height)) == (1200, 600)


def test_extract_scanned_renders_one_page_at_a_time(monkeypatch):
    calls: list[tuple[int, int]] = []

    def fake_info(_pdf_bytes):
        return {"Pages": 2}

    def fake_convert(_pdf_bytes, dpi=300, first_page=None, last_page=None):
        assert dpi == 300
        assert first_page == last_page
        calls.append((first_page, last_page))
        return [Image.new("RGB", (4, 4), "white")]

    class Line:
        text = "བོད"
        x = 0
        y = 0
        width = 1
        height = 1

    class Engine:
        ready = True
        error = None

        def run_on_image(self, image):
            assert image.ndim == 3
            return [Line()]

    monkeypatch.setattr("pdf2image.pdfinfo_from_bytes", fake_info)
    monkeypatch.setattr("pdf2image.convert_from_bytes", fake_convert)
    monkeypatch.setattr("app.pdf.ocr.get_engine", lambda: Engine())

    pages = extract_scanned(b"%PDF-fake")

    assert calls == [(1, 1), (2, 2)]
    assert [page.page_number for page in pages] == [1, 2]
    assert pages[0].text == "བོད"
    assert pages[0].is_scanned is True
