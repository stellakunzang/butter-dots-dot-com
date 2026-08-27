"""Unit tests for run_job CLI helpers and argument wiring."""
from pathlib import Path

import pytest
from PIL import Image

from app.ocr_assist import job_store
from app.ocr_assist.job_store import FINAL_TEXT_FILE, create_job, finalize_page, load_job, load_page
from app.ocr_assist.run_job import _parse_page_list, main
from app.ocr_assist.runner import OcrResult, run_all_pages


@pytest.fixture
def fake_pdf(monkeypatch):
    def _fake_render(pdf_bytes: bytes, *, dpi: int):
        return [Image.new("RGB", (40, 40), "white") for _ in range(3)]

    monkeypatch.setattr(job_store, "_render_pdf", _fake_render)
    return b"fake-pdf-bytes"


def test_parse_page_list_basic():
    assert _parse_page_list("3,7,12") == [3, 7, 12]
    assert _parse_page_list(" 1 , 2 ") == [1, 2]


def test_parse_page_list_rejects_bad_input():
    with pytest.raises(ValueError, match="empty"):
        _parse_page_list(" , ")
    with pytest.raises(ValueError, match="invalid"):
        _parse_page_list("1,x")
    with pytest.raises(ValueError, match=">= 1"):
        _parse_page_list("0,1")


def test_main_requires_pdf_or_job_id(capsys):
    assert main([]) == 1
    assert "pdf_path is required" in capsys.readouterr().err


def test_main_rerun_requires_job_id(capsys):
    assert main(["--rerun-pages", "1"]) == 1
    assert "--rerun-pages requires --job-id" in capsys.readouterr().err


def test_main_job_id_and_rerun_pages(tmp_path, fake_pdf, monkeypatch, capsys):
    job = create_job(
        fake_pdf,
        source_file="sample.pdf",
        baseline_settings={"model_variant": "Woodblock"},
        jobs_root=tmp_path,
    )
    finalize_page(job, 2, final_text="old page 2")
    finalize_page(job, 1, final_text="old page 1")

    ocr_calls: list[int] = []

    def fake_ocr(image_path: Path, settings: dict) -> OcrResult:
        # page-00N is the parent of image.png
        ocr_calls.append(int(image_path.parent.name.split("-")[1]))
        return OcrResult(text="བཀྲ་ཤིས་བདེ་ལེགས།", line_count=2)

    def fake_spellcheck(text: str):
        return []

    monkeypatch.setattr(
        "app.ocr_assist.runner._default_ocr_adapter",
        lambda: fake_ocr,
    )
    monkeypatch.setattr(
        "app.ocr_assist.runner._default_spellcheck_adapter",
        lambda: fake_spellcheck,
    )

    pdf = tmp_path / "unused.pdf"
    pdf.write_bytes(b"%PDF")

    rc = main(
        [
            "--jobs-root",
            str(tmp_path),
            "--job-id",
            job.id,
            "--rerun-pages",
            "2",
        ]
    )
    assert rc == 0
    assert ocr_calls == [2]
    reloaded = load_job(tmp_path, job.id)
    assert load_page(reloaded, 1).final_text == "old page 1"
    assert load_page(reloaded, 2).final_text is not None
    assert (reloaded.root / "page-002" / FINAL_TEXT_FILE).is_file()
    out = capsys.readouterr().out
    assert "reset page 2" in out
    assert "loaded job" in out
