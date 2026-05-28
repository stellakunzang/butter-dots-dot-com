"""
Filesystem-backed job store for the interactive OCR workflow.

A *job* is a single PDF (or, later, image set) being transcribed page by
page. State lives entirely under one directory per job, so a job is
inspectable by hand, resumable after a crash, and re-runnable per-page
without touching the rest. See ``docs/planning/INTERACTIVE_OCR_PLAN.md``
§ "Per-page state model" for the layout this module persists::

    jobs/<job_id>/
      manifest.json
      baseline_settings.json
      page-001/
        image.png
        settings.json
        attempts/
          01/{ocr.txt, quality.json, ai_verdict.json}
          02/...
        final.txt
        final_quality.json
        notes.md
      page-002/
        ...

The job store is deliberately schema-loose for OCR settings, quality, and
AI verdicts: those structures are owned by the runner (T-05),
quality scorer (T-03), and diagnostician (T-06) respectively. This module
just persists arbitrary dicts so adding a field upstream doesn't require
a job_store change.

All JSON writes go through ``_atomic_write_*`` (write-temp → ``os.replace``)
so a crash mid-write can't leave a half-written file on disk.
"""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


MANIFEST_FILE = "manifest.json"
BASELINE_SETTINGS_FILE = "baseline_settings.json"
PAGE_SETTINGS_FILE = "settings.json"
PAGE_IMAGE_FILE = "image.png"
FINAL_TEXT_FILE = "final.txt"
FINAL_QUALITY_FILE = "final_quality.json"
NOTES_FILE = "notes.md"
ATTEMPTS_DIR = "attempts"
ATTEMPT_OCR_FILE = "ocr.txt"
ATTEMPT_QUALITY_FILE = "quality.json"
ATTEMPT_VERDICT_FILE = "ai_verdict.json"

JOB_STATUS_IN_PROGRESS = "in_progress"
JOB_STATUS_COMPLETE = "complete"


@dataclass(frozen=True)
class AttemptRecord:
    """One OCR attempt on a page. Persisted under ``attempts/NN/``."""
    number: int
    ocr_text: str
    quality: dict[str, Any] | None = None
    ai_verdict: dict[str, Any] | None = None


@dataclass
class PageState:
    """All persisted state for one page of a job."""
    index: int
    image_path: Path
    settings: dict[str, Any]
    attempts: list[AttemptRecord] = field(default_factory=list)
    final_text: str | None = None
    final_quality: dict[str, Any] | None = None
    notes: str | None = None


@dataclass
class Job:
    """Top-level job metadata. Page state is loaded separately via ``load_page``."""
    id: str
    root: Path
    source_file: str
    baseline_settings: dict[str, Any]
    created_at: datetime
    page_count: int
    status: str


def create_job(
    pdf_bytes: bytes,
    source_file: str,
    baseline_settings: dict[str, Any],
    jobs_root: Path,
    *,
    job_id: str | None = None,
    dpi: int = 300,
) -> Job:
    """Render a PDF to per-page PNGs and persist the initial job state.

    Each page directory starts with a fresh copy of ``baseline_settings``
    in ``settings.json`` — retries mutate the page's copy only, never the
    job baseline. (See the plan's "Why this avoids the global-tweak
    regression" section.)
    """
    job_id = job_id or uuid.uuid4().hex[:12]
    job_dir = jobs_root / job_id
    # Refuse to clobber an existing job dir; caller picks a fresh id.
    job_dir.mkdir(parents=True, exist_ok=False)

    pil_pages = _render_pdf(pdf_bytes, dpi=dpi)
    page_count = len(pil_pages)
    created_at = datetime.now(timezone.utc)

    for i, pil_img in enumerate(pil_pages, start=1):
        page_dir = job_dir / _page_dir_name(i)
        page_dir.mkdir()
        pil_img.save(page_dir / PAGE_IMAGE_FILE, "PNG")
        _atomic_write_json(page_dir / PAGE_SETTINGS_FILE, dict(baseline_settings))
        (page_dir / ATTEMPTS_DIR).mkdir()

    _atomic_write_json(job_dir / BASELINE_SETTINGS_FILE, dict(baseline_settings))
    manifest = {
        "id": job_id,
        "source_file": source_file,
        "created_at": created_at.isoformat(),
        "page_count": page_count,
        "status": JOB_STATUS_IN_PROGRESS,
    }
    _atomic_write_json(job_dir / MANIFEST_FILE, manifest)

    return Job(
        id=job_id,
        root=job_dir,
        source_file=source_file,
        baseline_settings=dict(baseline_settings),
        created_at=created_at,
        page_count=page_count,
        status=JOB_STATUS_IN_PROGRESS,
    )


def load_job(jobs_root: Path, job_id: str) -> Job:
    """Read a job's manifest + baseline settings. Does not eagerly load pages."""
    job_dir = jobs_root / job_id
    if not job_dir.is_dir():
        raise FileNotFoundError(f"No job directory at {job_dir}")
    manifest = json.loads((job_dir / MANIFEST_FILE).read_text())
    baseline = json.loads((job_dir / BASELINE_SETTINGS_FILE).read_text())
    return Job(
        id=manifest["id"],
        root=job_dir,
        source_file=manifest["source_file"],
        baseline_settings=baseline,
        created_at=datetime.fromisoformat(manifest["created_at"]),
        page_count=manifest["page_count"],
        status=manifest["status"],
    )


def load_page(job: Job, page_index: int) -> PageState:
    """Read a single page's full state from disk."""
    page_dir = job.root / _page_dir_name(page_index)
    if not page_dir.is_dir():
        raise FileNotFoundError(f"No page directory: {page_dir}")

    settings = json.loads((page_dir / PAGE_SETTINGS_FILE).read_text())
    attempts_dir = page_dir / ATTEMPTS_DIR
    attempts = _load_attempts(attempts_dir) if attempts_dir.is_dir() else []

    final_text_path = page_dir / FINAL_TEXT_FILE
    final_text = final_text_path.read_text() if final_text_path.is_file() else None

    final_quality_path = page_dir / FINAL_QUALITY_FILE
    final_quality = (
        json.loads(final_quality_path.read_text())
        if final_quality_path.is_file()
        else None
    )

    notes_path = page_dir / NOTES_FILE
    notes = notes_path.read_text() if notes_path.is_file() else None

    return PageState(
        index=page_index,
        image_path=page_dir / PAGE_IMAGE_FILE,
        settings=settings,
        attempts=attempts,
        final_text=final_text,
        final_quality=final_quality,
        notes=notes,
    )


def save_page_attempt(
    job: Job,
    page_index: int,
    *,
    ocr_text: str,
    quality: dict[str, Any] | None = None,
    ai_verdict: dict[str, Any] | None = None,
) -> AttemptRecord:
    """Append a new attempt under ``attempts/NN/`` with monotonic numbering."""
    page_dir = job.root / _page_dir_name(page_index)
    if not page_dir.is_dir():
        raise FileNotFoundError(f"No page directory: {page_dir}")

    attempts_dir = page_dir / ATTEMPTS_DIR
    attempts_dir.mkdir(exist_ok=True)
    number = _next_attempt_number(attempts_dir)
    attempt_dir = attempts_dir / _attempt_dir_name(number)
    attempt_dir.mkdir()

    _atomic_write_text(attempt_dir / ATTEMPT_OCR_FILE, ocr_text)
    if quality is not None:
        _atomic_write_json(attempt_dir / ATTEMPT_QUALITY_FILE, quality)
    if ai_verdict is not None:
        _atomic_write_json(attempt_dir / ATTEMPT_VERDICT_FILE, ai_verdict)

    return AttemptRecord(
        number=number,
        ocr_text=ocr_text,
        quality=quality,
        ai_verdict=ai_verdict,
    )


def finalize_page(
    job: Job,
    page_index: int,
    *,
    final_text: str,
    final_quality: dict[str, Any] | None = None,
    notes: str | None = None,
) -> PageState:
    """Mark a page as finalized: write ``final.txt`` (+ quality, notes)."""
    page_dir = job.root / _page_dir_name(page_index)
    if not page_dir.is_dir():
        raise FileNotFoundError(f"No page directory: {page_dir}")

    _atomic_write_text(page_dir / FINAL_TEXT_FILE, final_text)
    if final_quality is not None:
        _atomic_write_json(page_dir / FINAL_QUALITY_FILE, final_quality)
    if notes is not None:
        _atomic_write_text(page_dir / NOTES_FILE, notes)

    return load_page(job, page_index)


def list_jobs(jobs_root: Path) -> list[Job]:
    """Return every readable job under ``jobs_root`` (skip malformed dirs)."""
    if not jobs_root.is_dir():
        return []
    jobs: list[Job] = []
    for entry in sorted(jobs_root.iterdir()):
        if not entry.is_dir() or not (entry / MANIFEST_FILE).is_file():
            continue
        try:
            jobs.append(load_job(jobs_root, entry.name))
        except (json.JSONDecodeError, KeyError):
            continue
    return jobs


def _page_dir_name(index: int) -> str:
    return f"page-{index:03d}"


def _attempt_dir_name(n: int) -> str:
    return f"{n:02d}"


def _next_attempt_number(attempts_dir: Path) -> int:
    nums = [
        int(entry.name)
        for entry in attempts_dir.iterdir()
        if entry.is_dir() and entry.name.isdigit()
    ]
    return max(nums) + 1 if nums else 1


def _load_attempts(attempts_dir: Path) -> list[AttemptRecord]:
    records: list[AttemptRecord] = []
    for entry in sorted(attempts_dir.iterdir(), key=lambda p: p.name):
        if not entry.is_dir() or not entry.name.isdigit():
            continue
        ocr_path = entry / ATTEMPT_OCR_FILE
        quality_path = entry / ATTEMPT_QUALITY_FILE
        verdict_path = entry / ATTEMPT_VERDICT_FILE
        records.append(
            AttemptRecord(
                number=int(entry.name),
                ocr_text=ocr_path.read_text() if ocr_path.is_file() else "",
                quality=json.loads(quality_path.read_text()) if quality_path.is_file() else None,
                ai_verdict=json.loads(verdict_path.read_text()) if verdict_path.is_file() else None,
            )
        )
    return records


def _atomic_write_text(path: Path, content: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content)
    os.replace(tmp, path)


def _atomic_write_json(path: Path, obj: Any) -> None:
    _atomic_write_text(path, json.dumps(obj, indent=2, sort_keys=True))


def _render_pdf(pdf_bytes: bytes, *, dpi: int) -> Sequence:
    """Render a PDF to PIL images. Pulled out for monkeypatching in tests."""
    from pdf2image import convert_from_bytes
    return convert_from_bytes(pdf_bytes, dpi=dpi)
