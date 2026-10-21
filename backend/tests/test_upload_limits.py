"""Bounds and input checks on the public PDF upload endpoint."""
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.spellcheck import _download_filename, _reject_declared_length
from app.main import app

client = TestClient(app)


def _pdf_bytes() -> bytes:
    import fitz

    doc = fitz.open()
    doc.new_page()
    data = doc.tobytes()
    doc.close()
    return data


def _upload(data: bytes, filename: str = "page.pdf", **form):
    return client.post(
        "/api/v1/spellcheck/upload",
        files={"file": (filename, data, "application/pdf")},
        data=form,
    )


class TestUploadValidation:
    def test_non_pdf_bytes_are_rejected(self):
        response = _upload(b"not a pdf")
        assert response.status_code == 400
        assert "not a pdf" not in response.text

    def test_oversize_body_is_rejected(self, monkeypatch):
        monkeypatch.setattr("app.api.spellcheck.MAX_UPLOAD_BYTES", 8)
        response = _upload(b"%PDF-" + b"x" * 20)
        assert response.status_code == 413

    def test_declared_content_length_over_cap(self):
        class Request:
            headers = {"content-length": str(60 * 1024 * 1024)}

        with pytest.raises(HTTPException) as exc:
            _reject_declared_length(Request())  # type: ignore[arg-type]
        assert exc.value.status_code == 413

    def test_page_cap(self, monkeypatch):
        monkeypatch.setattr("app.api.spellcheck.MAX_PAGES", 0)
        response = _upload(_pdf_bytes())
        assert response.status_code == 413
        assert "page limit" in response.json()["detail"]

    def test_invalid_email(self):
        response = _upload(_pdf_bytes(), email="not-an-email")
        assert response.status_code == 422
        assert response.json()["detail"] == "Invalid email address"

    def test_unreadable_pdf_hides_parser_error(self):
        response = _upload(b"%PDF-not-really")
        assert response.status_code == 422
        assert response.json()["detail"] == "Could not read PDF"


def test_download_filename_strips_header_and_path():
    assert _download_filename("book.pdf", suffix=".pdf") == "spellcheck_book.pdf"
    name = _download_filename('a\r\n"b.pdf', suffix=".docx")
    assert "\r" not in name
    assert "\n" not in name
    assert '"' not in name
    assert _download_filename("../../etc/passwd", suffix=".pdf") == "spellcheck_passwd.pdf"
