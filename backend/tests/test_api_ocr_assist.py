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
    # Create must report running so the UI starts polling before BackgroundTasks
    # begin (they only run after the response is sent).
    assert body["running"] is True

    # BackgroundTasks run after response in TestClient; poll until not running.
    status = client.get(f"/api/v1/ocr-assist/jobs/{job_id}")
    assert status.status_code == 200
    data = status.json()
    assert len(data["pages"]) == 2
    assert all(p["status"] == "final" for p in data["pages"])
    assert data["running"] is False
    assert data["docx_ready"] is True

    docx = client.get(f"/api/v1/ocr-assist/jobs/{job_id}/docx")
    assert docx.status_code == 200
    assert docx.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument"
    )


def test_docx_available_with_partial_acceptance(client):
    """Partial finals still expose Download DOCX (accepted pages only)."""
    from app.api import ocr_assist as ocr_assist_api

    resp = client.post(
        "/api/v1/ocr-assist/jobs",
        files={"file": ("t.pdf", b"%PDF-fake", "application/pdf")},
    )
    job_id = resp.json()["id"]
    assert client.get(f"/api/v1/ocr-assist/jobs/{job_id}").json()["docx_ready"] is True

    job = job_store.load_job(ocr_assist_api._jobs_root(), job_id)
    job_store.reset_page(job, 2)

    status = client.get(f"/api/v1/ocr-assist/jobs/{job_id}")
    assert status.status_code == 200
    data = status.json()
    assert data["docx_ready"] is True
    assert [p["status"] for p in data["pages"]] == ["final", "needs_review"]

    docx = client.get(f"/api/v1/ocr-assist/jobs/{job_id}/docx")
    assert docx.status_code == 200
    assert docx.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument"
    )


def _read_jsonl(path: Path) -> list[dict]:
    import json

    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_accept_and_compare_vision(client, monkeypatch, tmp_path):
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

    from app.api import ocr_assist as ocr_assist_api

    job = job_store.load_job(ocr_assist_api._jobs_root(), job_id)
    page_lines = _read_jsonl(job.root / "page-001" / "interventions.jsonl")
    job_lines = _read_jsonl(job.root / "interventions.jsonl")
    assert len(page_lines) == 1
    assert page_lines[0]["kind"] == "accept_vision"
    assert page_lines[0]["provider"] == "gemini"
    assert page_lines[0]["source"] == "human_ui"
    assert page_lines[0]["quality_after"] is None
    assert page_lines[0]["quality_before"] is not None
    assert job_lines == page_lines


def test_retry_with_flags_updates_settings_and_logs_intervention(client, tmp_path):
    from app.api import ocr_assist as ocr_assist_api

    resp = client.post(
        "/api/v1/ocr-assist/jobs",
        files={"file": ("t.pdf", b"%PDF-fake", "application/pdf")},
    )
    job_id = resp.json()["id"]
    job = job_store.load_job(ocr_assist_api._jobs_root(), job_id)
    page_before = job_store.load_page(job, 1)
    attempts_before = len(page_before.attempts)

    retry = client.post(
        f"/api/v1/ocr-assist/jobs/{job_id}/pages/1/action",
        json={"action": "retry", "use_tps": True, "rotate": 90},
    )
    assert retry.status_code == 200, retry.text
    body = retry.json()
    assert body["settings"]["use_tps"] is True
    assert float(body["settings"]["rotate"]) == 90.0
    assert len(body["attempts"]) == attempts_before + 1

    settings_on_disk = job_store.load_page(job, 1).settings
    assert settings_on_disk["use_tps"] is True
    assert float(settings_on_disk["rotate"]) == 90.0

    page_iv = job.root / "page-001" / "interventions.jsonl"
    job_iv = job.root / "interventions.jsonl"
    assert page_iv.is_file(), f"missing {page_iv}; jobs_root={ocr_assist_api._jobs_root()} job.root={job.root} listing={[p.name for p in job.root.rglob('*')]}"
    page_lines = _read_jsonl(page_iv)
    job_lines = _read_jsonl(job_iv)
    assert len(page_lines) == 1, page_lines
    rec = page_lines[0]
    assert rec["kind"] == "retry_with_flags"
    assert rec["source"] == "human_ui"
    assert rec["flags"] == {"use_tps": True, "rotate": 90.0}
    assert rec["settings_after"]["use_tps"] is True
    assert float(rec["settings_after"]["rotate"]) == 90.0
    assert rec["quality_before"] is not None
    assert rec["quality_after"] is not None
    assert job_lines == page_lines


def test_accept_and_edit_accept_log_interventions(client, tmp_path):
    resp = client.post(
        "/api/v1/ocr-assist/jobs",
        files={"file": ("t.pdf", b"%PDF-fake", "application/pdf")},
    )
    job_id = resp.json()["id"]

    # Force needs_review so accept/edit are meaningful after auto-finalize.
    from app.api import ocr_assist as ocr_assist_api

    job = job_store.load_job(ocr_assist_api._jobs_root(), job_id)
    job_store.reset_page(job, 1)

    accept = client.post(
        f"/api/v1/ocr-assist/jobs/{job_id}/pages/1/action",
        json={"action": "accept"},
    )
    assert accept.status_code == 200, accept.text

    job_store.reset_page(job, 1)
    edit = client.post(
        f"/api/v1/ocr-assist/jobs/{job_id}/pages/1/action",
        json={"action": "edit_accept", "text": "edited text"},
    )
    assert edit.status_code == 200, edit.text
    assert edit.json()["final_text"] == "edited text"

    page_lines = _read_jsonl(job.root / "page-001" / "interventions.jsonl")
    kinds = [r["kind"] for r in page_lines]
    assert kinds == ["accept", "edit_accept"]
    for rec in page_lines:
        assert rec["source"] == "human_ui"
        assert rec["quality_before"] is not None
        assert rec["quality_after"] is None
        assert rec["flags"] is None


def test_compare_vision_respects_providers_filter(client, monkeypatch):
    calls: list[str] = []

    def factory(provider: str):
        def _call(*, image_path: Path) -> VisionTranscript:
            calls.append(provider)
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
        json={"action": "compare_vision", "providers": ["gemini"]},
    )
    assert compare.status_code == 200, compare.text
    results = compare.json()["compare"]["results"]
    assert [r["provider"] for r in results] == ["gemini"]
    assert calls == ["gemini"]


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
