"""Tests for on-demand dual vision compare."""
from pathlib import Path

import pytest
from PIL import Image

from app.ocr_assist import job_store
from app.ocr_assist.compare_vision import compare_vision_providers
from app.ocr_assist.contracts import VisionTranscript
from app.ocr_assist.job_store import create_job, load_page, save_vision_transcript


@pytest.fixture
def fake_pdf(monkeypatch):
    def _fake_render(pdf_bytes: bytes, *, dpi: int):
        return [Image.new("RGB", (40, 40), "white") for _ in range(2)]

    monkeypatch.setattr(job_store, "_render_pdf", _fake_render)
    return b"fake-pdf-bytes"


@pytest.fixture
def job(tmp_path: Path, fake_pdf):
    return create_job(
        fake_pdf,
        source_file="sample.pdf",
        baseline_settings={"model_variant": "Woodblock"},
        jobs_root=tmp_path,
    )


def test_save_and_load_provider_keyed_vision(job):
    save_vision_transcript(
        job,
        1,
        transcript={"text": "claude", "notes": None},
        quality={"composite_score": 0.8},
        spellcheck_errors=[{"word": "x", "error_type": "unknown_word"}],
        provider="anthropic",
    )
    save_vision_transcript(
        job,
        1,
        transcript={"text": "gemini", "notes": None},
        quality={"composite_score": 0.9},
        provider="gemini",
    )
    page = load_page(job, 1)
    assert page.vision_by_provider["anthropic"]["transcript"]["text"] == "claude"
    assert page.vision_by_provider["anthropic"]["spellcheck_errors"][0]["word"] == "x"
    assert page.vision_by_provider["gemini"]["quality"]["composite_score"] == 0.9
    assert page.vision_by_provider["gemini"]["spellcheck_errors"] is None
    assert page.vision_transcript is None  # legacy path unused


def test_compare_vision_runs_both_providers(job):
    def factory(provider: str):
        text = "བཀྲ་ཤིས།" if provider == "anthropic" else "བདེ་ལེགས།"

        def _call(*, image_path: Path) -> VisionTranscript:
            assert image_path.is_file()
            return VisionTranscript(text=text, notes=f"from {provider}")

        return _call

    result = compare_vision_providers(
        job,
        1,
        providers=("anthropic", "gemini"),
        spellcheck=lambda text: [{"word": "stub", "error_type": "unknown_word"}],
        transcriber_factory=factory,
    )
    assert {r.provider for r in result.results} == {"anthropic", "gemini"}
    assert all(r.error is None for r in result.results)
    assert all(r.composite_score is not None for r in result.results)
    assert all(r.spellcheck_errors for r in result.results)

    page = load_page(job, 1)
    assert "anthropic" in page.vision_by_provider
    assert "gemini" in page.vision_by_provider
    assert page.vision_by_provider["anthropic"]["transcript"]["text"] == "བཀྲ་ཤིས།"
    assert page.vision_by_provider["anthropic"]["spellcheck_errors"][0]["word"] == "stub"


def test_compare_vision_isolates_provider_errors(job):
    def factory(provider: str):
        if provider == "gemini":
            raise RuntimeError("GEMINI_API_KEY not set")

        def _call(*, image_path: Path) -> VisionTranscript:
            return VisionTranscript(text="བཀྲ་ཤིས།", notes=None)

        return _call

    result = compare_vision_providers(
        job,
        1,
        providers=("anthropic", "gemini"),
        spellcheck=lambda text: [],
        transcriber_factory=factory,
    )
    by = result.by_provider()
    assert by["anthropic"].error is None
    assert by["anthropic"].transcript is not None
    assert by["gemini"].error is not None
    assert "GEMINI_API_KEY" in by["gemini"].error
