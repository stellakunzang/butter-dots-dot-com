"""Unit tests for run_job._print_summary."""
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from app.ocr_assist.job_store import PageState
from app.ocr_assist.quality import PageQuality
from app.ocr_assist.runner import RunResult
from app.ocr_assist.run_job import _print_summary


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
    )


def test_print_summary_mixed(capsys):
    results = [
        RunResult(page=_make_page(0), decision="accept", quality=_make_quality(0.95), verdict="accept"),
        RunResult(page=_make_page(1), decision="needs_review", quality=_make_quality(0.42), verdict="escalate"),
        RunResult(page=_make_page(2), decision="error", quality=None, error="timeout"),
    ]

    _print_summary(results)

    captured = capsys.readouterr().out
    assert "1 accepted" in captured
    assert "1 needs review" in captured
    assert "1 errored" in captured
    assert "composite=0.950" in captured
    assert "composite=0.420" in captured
    assert "error=timeout" in captured
    # error row must NOT try to print composite_score
    lines = [l for l in captured.splitlines() if "page   2" in l]
    assert len(lines) == 1
    assert "composite" not in lines[0]
