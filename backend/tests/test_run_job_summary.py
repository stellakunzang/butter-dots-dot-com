"""Unit tests for run_job._print_summary."""
from datetime import datetime, timezone
from pathlib import Path

from app.ocr_assist.job_store import Job, PageState
from app.ocr_assist.quality import PageQuality
from app.ocr_assist.runner import RunResult
from app.ocr_assist.run_job import _maybe_open_artifacts, _print_job_banner, _print_summary


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
        plus_sign_count=0,
        repetition_run_length=0,
        repetition_char="",
        mean_syllables_per_line=10.0,
        short_line_ratio=0.0,
        ocr_confidence=score,
    )


def _make_job(tmp_path: Path, *, with_docx: bool = False) -> Job:
    job_root = tmp_path / "jobdir"
    job_root.mkdir()
    if with_docx:
        (job_root / "output.docx").write_bytes(b"PK")
    return Job(
        id="deadbeefcafe",
        root=job_root,
        source_file="x.pdf",
        baseline_settings={},
        created_at=datetime.now(timezone.utc),
        page_count=2,
        status="in_progress",
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
    job = _make_job(tmp_path)
    _print_job_banner("created", job)
    out = capsys.readouterr().out
    assert "created job" in out
    assert "job-id:     deadbeefcafe" in out
    assert "directory:" in out
    assert str(job.root.resolve()) in out
    assert "output.docx" in out


def test_maybe_open_artifacts_open_and_reveal(capsys, tmp_path):
    job = _make_job(tmp_path, with_docx=True)
    calls: list[list[str]] = []

    def fake_run(argv, check=False):
        calls.append(list(argv))
        return None

    _maybe_open_artifacts(
        job,
        open_docx=True,
        reveal=True,
        platform="darwin",
        runner=fake_run,
    )
    out = capsys.readouterr().out
    root = str(job.root.resolve())
    docx = str((job.root / "output.docx").resolve())
    assert ["open", "-R", root] in calls
    assert ["open", docx] in calls
    assert "revealing job directory" in out
    assert "opening docx:" in out


def test_maybe_open_artifacts_missing_docx(capsys, tmp_path):
    job = _make_job(tmp_path, with_docx=False)
    calls: list[list[str]] = []

    def fake_run(argv, check=False):
        calls.append(list(argv))
        return None

    _maybe_open_artifacts(
        job,
        open_docx=True,
        reveal=False,
        platform="darwin",
        runner=fake_run,
    )
    err = capsys.readouterr().err
    assert calls == []
    assert "--open requested but no docx" in err


def test_maybe_open_artifacts_noop_when_flags_off(tmp_path):
    job = _make_job(tmp_path, with_docx=True)
    calls: list[list[str]] = []

    def fake_run(argv, check=False):
        calls.append(list(argv))
        return None

    _maybe_open_artifacts(
        job,
        open_docx=False,
        reveal=False,
        platform="darwin",
        runner=fake_run,
    )
    assert calls == []


def test_maybe_open_artifacts_skips_non_darwin(capsys, tmp_path):
    job = _make_job(tmp_path, with_docx=True)
    calls: list[list[str]] = []

    def fake_run(argv, check=False):
        calls.append(list(argv))
        return None

    _maybe_open_artifacts(
        job,
        open_docx=True,
        reveal=True,
        platform="linux",
        runner=fake_run,
    )
    err = capsys.readouterr().err
    assert calls == []
    assert "macOS-only" in err
