"""
Tests for the per-page OCR runner (T-05).

Covers the T-05 acceptance criteria:
- End-to-end run on a small (faked) PDF produces a populated job directory.
- High-score pages auto-accept (final.txt written); low-score pages have
  status needs_review (final.txt absent but attempt persisted).
- No retries happen when claude_diagnostician is None.
- run_all_pages skips pages already finalized on disk (resume).

OCR and spellcheck are injected as fakes so the suite never loads BDRC models
or opens a database connection.
"""
from pathlib import Path

import pytest
from PIL import Image

from app.ocr_assist import job_store
from app.ocr_assist.job_store import (
    create_job,
    load_page,
    save_page_attempt,
    finalize_page,
)
from app.ocr_assist.quality import Thresholds
from app.ocr_assist.runner import (
    DEFAULT_THRESHOLDS,
    OcrResult,
    run_all_pages,
    run_page,
)


CLEAN_TEXT = "བཀྲ་ཤིས་བདེ་ལེགས།\nདགེ་བའི་བཤེས་གཉེན།"
GARBLED_TEXT = "xxxx hello yyy zzz totally not tibetan at all"


@pytest.fixture
def fake_pdf(monkeypatch):
    """Bypass pdf2image: render to a small list of in-memory PIL images."""
    def _fake_render(pdf_bytes: bytes, *, dpi: int):
        return [Image.new("RGB", (40, 40), "white") for _ in range(3)]

    monkeypatch.setattr(job_store, "_render_pdf", _fake_render)
    return b"fake-pdf-bytes"


@pytest.fixture
def job(tmp_path: Path, fake_pdf):
    return create_job(
        fake_pdf,
        source_file="sample.pdf",
        baseline_settings={"model_variant": "Modern"},
        jobs_root=tmp_path,
    )


def clean_ocr(image_path: Path, settings: dict) -> OcrResult:
    return OcrResult(text=CLEAN_TEXT, line_count=2)


def garbled_ocr(image_path: Path, settings: dict) -> OcrResult:
    return OcrResult(text=GARBLED_TEXT, line_count=1)


def no_errors(text: str) -> list[dict]:
    return []


def class_errors(text: str) -> list[dict]:
    return [
        {"word": "xxx", "error_type": "invalid_subscript_combination", "severity": "critical"},
    ]


class TestRunPageAccept:
    def test_clean_page_finalizes(self, job):
        result = run_page(job, 1, ocr=clean_ocr, spellcheck=no_errors)

        assert result.decision == "accept"
        assert result.page.final_text == CLEAN_TEXT
        assert result.quality.composite_score > 0.95
        assert (job.root / "page-001" / "final.txt").is_file()

    def test_attempt_persisted_for_accepted_page(self, job):
        run_page(job, 1, ocr=clean_ocr, spellcheck=no_errors)
        page = load_page(job, 1)
        assert len(page.attempts) == 1
        assert page.attempts[0].ocr_text == CLEAN_TEXT
        assert page.attempts[0].quality is not None
        assert page.attempts[0].quality["composite_score"] > 0.95


class TestRunPageNeedsReview:
    def test_low_score_page_does_not_finalize(self, job):
        # All-non-Tibetan text pegs non_tibetan_char_ratio at 1.0 → composite=0.75
        # (penalty 0.25), between reject=0.5 and accept=0.85, so decide() escalates.
        result = run_page(job, 1, ocr=garbled_ocr, spellcheck=no_errors)

        assert result.decision == "needs_review"
        assert result.page.final_text is None
        assert not (job.root / "page-001" / "final.txt").is_file()

    def test_needs_review_still_records_attempt(self, job):
        run_page(job, 1, ocr=garbled_ocr, spellcheck=no_errors)
        page = load_page(job, 1)
        assert len(page.attempts) == 1
        assert page.attempts[0].ocr_text == GARBLED_TEXT

    def test_encoding_error_blocks_accept_even_at_high_score(self, job):
        # Clean text + a single encoding_error severity=critical → hard floor
        # in `decide` forces escalate.
        def bad_spellcheck(text: str) -> list[dict]:
            return [{
                "word": "བཀྲ",
                "error_type": "encoding_error",
                "severity": "critical",
            }]

        result = run_page(job, 1, ocr=clean_ocr, spellcheck=bad_spellcheck)
        assert result.decision == "needs_review"
        assert result.page.final_text is None


class TestNoRetries:
    def test_diagnostician_arg_rejected_until_t06(self, job):
        # Until T-06 wires the loop, silently ignoring the diagnostician arg
        # would lull callers into believing retries are running. The runner
        # refuses the call instead.
        with pytest.raises(NotImplementedError):
            run_page(
                job,
                1,
                ocr=garbled_ocr,
                spellcheck=no_errors,
                claude_diagnostician=lambda *a, **kw: None,
            )

    def test_low_score_only_one_attempt(self, job):
        # A bad page produces exactly one OCR attempt: no retry loop runs.
        calls = []

        def counting_ocr(image_path: Path, settings: dict) -> OcrResult:
            calls.append(image_path)
            return OcrResult(text=GARBLED_TEXT, line_count=1)

        run_page(job, 1, ocr=counting_ocr, spellcheck=no_errors)
        assert len(calls) == 1


class TestRunAllPages:
    def test_runs_every_page(self, job):
        results = run_all_pages(job, ocr=clean_ocr, spellcheck=no_errors)
        assert len(results) == job.page_count
        assert all(r.decision == "accept" for r in results)
        for i in range(1, job.page_count + 1):
            assert (job.root / f"page-{i:03d}" / "final.txt").is_file()

    def test_skips_already_finalized_pages(self, job):
        # Pre-finalize page 2 by hand; runner should not OCR it on the next pass.
        finalize_page(
            job,
            2,
            final_text="manually finalized",
            final_quality={"composite_score": 1.0},
        )

        ocr_calls: list[Path] = []

        def counting_ocr(image_path: Path, settings: dict) -> OcrResult:
            ocr_calls.append(image_path)
            return OcrResult(text=CLEAN_TEXT, line_count=2)

        results = run_all_pages(job, ocr=counting_ocr, spellcheck=no_errors)

        # Page 2 was already final → 2 pages OCR'd (pages 1 and 3), not 3.
        assert len(ocr_calls) == 2
        assert {r.page.index for r in results} == {1, 3}
        # Pre-finalized text is preserved.
        assert load_page(job, 2).final_text == "manually finalized"


class TestThresholdsOverride:
    def test_lax_thresholds_accept_garbled(self, job):
        # The garbled page is rejected under DEFAULT_THRESHOLDS (see
        # TestRunPageNeedsReview); lowering accept to 0 flips it to accept.
        lax = Thresholds(accept=0.0, reject=0.0)
        result = run_page(
            job, 1, ocr=garbled_ocr, spellcheck=no_errors, thresholds=lax
        )
        assert result.decision == "accept"
        assert result.page.final_text == GARBLED_TEXT


class TestDefaultThresholds:
    def test_defaults_match_t03_test_values(self):
        # Sanity guard: T-10 calibrates these — when that ticket lands,
        # the new values should be documented and this test updated.
        assert DEFAULT_THRESHOLDS.accept == 0.85
        assert DEFAULT_THRESHOLDS.reject == 0.5
