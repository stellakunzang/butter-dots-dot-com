"""Append-only human intervention log for interactive OCR.

Records Retry-with-flags and accept/edit outcomes so high-confidence-but-wrong
pages become labeled data for a future cheap second-stage gate. See
``docs/planning/INTERACTIVE_OCR_PLAN.md`` Living decisions.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.ocr_assist.job_store import Job, _page_dir_name

PAGE_INTERVENTIONS_FILE = "interventions.jsonl"
JOB_INTERVENTIONS_FILE = "interventions.jsonl"

_QUALITY_KEYS = (
    "ocr_confidence",
    "sanskrit_adjusted_error_ratio",
    "unknown_word_ratio",
    "tibetan_syllable_count",
    "composite_score",
)


def quality_snapshot(quality: dict[str, Any] | None) -> dict[str, Any] | None:
    """Compact quality fields for intervention rows."""
    if not quality:
        return None
    return {k: quality.get(k) for k in _QUALITY_KEYS if k in quality}


def append_intervention(
    job: Job,
    page_index: int,
    *,
    kind: str,
    flags: dict[str, Any] | None = None,
    settings_before: dict[str, Any] | None = None,
    settings_after: dict[str, Any] | None = None,
    quality_before: dict[str, Any] | None = None,
    quality_after: dict[str, Any] | None = None,
    provider: str | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    """Append one intervention line to page + job JSONL files.

    Returns the record that was written.
    """
    record: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "kind": kind,
        "page_index": page_index,
        "source": "human_ui",
        "flags": flags,
        "settings_before": settings_before,
        "settings_after": settings_after,
        "quality_before": quality_snapshot(quality_before),
        "quality_after": quality_snapshot(quality_after),
        "provider": provider,
    }
    if error is not None:
        record["error"] = error

    line = json.dumps(record, ensure_ascii=False) + "\n"
    page_dir = job.root / _page_dir_name(page_index)
    page_dir.mkdir(parents=True, exist_ok=True)
    _append_line(page_dir / PAGE_INTERVENTIONS_FILE, line)
    _append_line(job.root / JOB_INTERVENTIONS_FILE, line)
    return record


def _append_line(path: Path, line: str) -> None:
    """Append UTF-8 line and fsync so a crash doesn't lose the record."""
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line)
        fh.flush()
        os.fsync(fh.fileno())
