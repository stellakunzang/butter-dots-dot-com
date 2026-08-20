"""API tests for local ocr-assist routes (OCR_ASSIST_LOCAL)."""
from pathlib import Path

import pytest
from PIL import Image
from fastapi.testclient import TestClient

from app.ocr_assist import job_store
from app.ocr_assist.contracts import VisionTranscript
from app.ocr_assist.runner import OcrResult


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("OCR_ASSIST_LOCAL", "true")
    monkeypatch.setenv("OCR_ASSIST_JOBS_ROOT", str(tmp_path))

    def _fake_render(pdf_bytes: bytes, *, dpi: int):
        return [Image.new("RGB", (40, 40), "white") for _ in range(2)]

    monkeypatch.setattr(job_store, "_render_pdf", _fake_render)

    def fake_ocr(image_path: Path, settings: dict) -> OcrResult:
        return OcrResult(text="བཀྲ་ཤིས་བདེ་ལེགས།", line_count=1)

    monkeypatch.setattr(
        "app.ocr_assist.runner._default_ocr_adapter",
        lambda: fake_ocr,
    )
    monkeypatch.setattr(
        "app.ocr_assist.runner._default_spellcheck_adapter",
        lambda: (lambda text: []),
    )

    # Settings/app are imported at module load — re-import after env change.
    import importlib

    import app.config as config_mod
    import app.main as main_mod
    importlib.reload(config_mod)
    importlib.reload(main_mod)

    with TestClient(main_mod.app) as c:
        yield c

    # Restore default settings for other tests in the same session.
    monkeypatch.delenv("OCR_ASSIST_LOCAL", raising=False)
    monkeypatch.delenv("OCR_ASSIST_JOBS_ROOT", raising=False)
    importlib.reload(config_mod)
    importlib.reload(main_mod)


def test_create_job_and_poll(client, tmp_path):
    resp = client.post(
        "/api/v1/ocr-assist/jobs",
        files={"file": ("t.pdf", b"%PDF-fake", "application/pdf")},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    job_id = body["id"]
    assert body["page_count"] == 2

    # BackgroundTasks run after response in TestClient; poll until not running.
    status = client.get(f"/api/v1/ocr-assist/jobs/{job_id}")
    assert status.status_code == 200
    data = status.json()
    assert len(data["pages"]) == 2
    assert all(p["status"] == "final" for p in data["pages"])

    docx = client.get(f"/api/v1/ocr-assist/jobs/{job_id}/docx")
    assert docx.status_code == 200
    assert docx.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument"
    )


def test_accept_and_compare_vision(client, monkeypatch):
    def factory(provider: str):
        def _call(*, image_path: Path) -> VisionTranscript:
            return VisionTranscript(text=f"vision-{provider}", notes=None)

        return _call

    monkeypatch.setattr(
        "app.ocr_assist.compare_vision.build_vision_transcriber",
        factory,
    )

    resp = client.post(
        "/api/v1/ocr-assist/jobs",
        files={"file": ("t.pdf", b"%PDF-fake", "application/pdf")},
    )
    job_id = resp.json()["id"]

    compare = client.post(
        f"/api/v1/ocr-assist/jobs/{job_id}/pages/1/action",
        json={"action": "compare_vision"},
    )
    assert compare.status_code == 200, compare.text
    providers = {r["provider"] for r in compare.json()["compare"]["results"]}
    assert providers == {"anthropic", "gemini"}

    accept = client.post(
        f"/api/v1/ocr-assist/jobs/{job_id}/pages/1/action",
        json={"action": "accept_vision", "provider": "gemini"},
    )
    assert accept.status_code == 200, accept.text
    assert accept.json()["final_text"] == "vision-gemini"
    assert accept.json()["status"] == "final"


def test_routes_absent_when_flag_off(monkeypatch):
    monkeypatch.setenv("OCR_ASSIST_LOCAL", "false")
    import importlib
    import app.config as config_mod
    import app.main as main_mod

    importlib.reload(config_mod)
    importlib.reload(main_mod)
    with TestClient(main_mod.app) as c:
        resp = c.post(
            "/api/v1/ocr-assist/jobs",
            files={"file": ("t.pdf", b"%PDF", "application/pdf")},
        )
        assert resp.status_code == 404
    monkeypatch.delenv("OCR_ASSIST_LOCAL", raising=False)
    importlib.reload(config_mod)
    importlib.reload(main_mod)
