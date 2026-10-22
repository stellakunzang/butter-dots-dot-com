"""Scanned extraction renders a single page image at a time."""

from PIL import Image

from app.pdf.extractor import extract_scanned


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
