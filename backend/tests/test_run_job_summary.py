"""Unit tests for run_job._print_summary."""
from datetime import datetime, timezone
from pathlib import Path

from app.ocr_assist.job_store import Job, PageState
from app.ocr_assist.quality import PageQuality
from app.ocr_assist.runner import RunResult
from app.ocr_assist.run_job import _print_job_banner, _print_summary


def _make_page(index: int) -> PageState:
    return PageState(index=index, image_path=Path(f"/fake/{index}.png"), settings={})


def _make_quality(score: float = 0.9) -> PageQuality:
    return PageQuality(
        non_tibetan_char_ratio=0.0,
        structural_error_ratio=0.0,
        sanskrit_adjusted_error_ratio=0.0,
        line_count_sanity=1.0,
        encoding_error_count=0,
        unknown_word_ratio=0.0,
        composite_score=score,
        breakdown={},
        tibetan_only_composite_score=score,
        tibetan_syllable_count=10,
        latin_letter_count=0,
        repetition_run_length=0,
        repetition_char="",
    )


def test_print_summary_mixed(capsys, tmp_path):
    job_root = tmp_path / "abc123def456"
    job_root.mkdir()
    job = Job(
        id="abc123def456",
        root=job_root,
        source_file="book.pdf",
        baseline_settings={},
        created_at=datetime.now(timezone.utc),
        page_count=3,
        status="in_progress",
    )
    (job_root / "output.docx").write_bytes(b"PK")

    results = [
        RunResult(page=_make_page(0), decision="accept", quality=_make_quality(0.95), verdict="accept"),
        RunResult(page=_make_page(1), decision="needs_review", quality=_make_quality(0.42), verdict="escalate"),
        RunResult(page=_make_page(2), decision="error", quality=None, error="timeout"),
    ]

    _print_summary(results, job=job)

    captured = capsys.readouterr().out
    assert "1 accepted" in captured
    assert "1 needs review" in captured
    assert "1 error" in captured
    assert "composite=0.950" in captured
    assert "composite=0.420" in captured
    assert "error=timeout" in captured
    # error row must NOT try to print composite_score
    lines = [l for l in captured.splitlines() if "page   2" in l]
    assert len(lines) == 1
    assert "composite" not in lines[0]
    assert "job-id:     abc123def456" in captured
    assert "docx:" in captured
    assert str((job_root / "output.docx").resolve()) in captured


def test_print_job_banner(capsys, tmp_path):
    job_root = tmp_path / "jobdir"
    job_root.mkdir()
    job = Job(
        id="deadbeefcafe",
        root=job_root,
        source_file="x.pdf",
        baseline_settings={},
        created_at=datetime.now(timezone.utc),
        page_count=2,
        status="in_progress",
    )
    _print_job_banner("created", job)
    out = capsys.readouterr().out
    assert "created job" in out
    assert "job-id:     deadbeefcafe" in out
    assert "directory:" in out
    assert str(job_root.resolve()) in out
    assert "output.docx" in out
