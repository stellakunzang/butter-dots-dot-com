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

All text/JSON is read and written as UTF-8 regardless of the host's locale
so Tibetan/Sanskrit transcriptions round-trip correctly everywhere (the
platform default is cp1252 on a stock Windows install, which would corrupt
the script). JSON is stored with ``ensure_ascii=False`` so the files stay
human-inspectable.

All writes go through ``_atomic_write_*``: content is written to a unique
temp file, ``fsync``'d, then ``os.replace``'d into place (and the parent
directory is ``fsync``'d), so a crash mid-write can't leave a half-written
or partially-flushed file on disk. The store assumes a *single writer per
job*: it serializes nothing, so concurrent writers to the same job (e.g. a
future parallelizing runner) must coordinate externally.
"""
from __future__ import annotations

import json
import os
import tempfile
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
# T-07 vision-OCR fallback transcripts live directly under the page dir, not
# under attempts/: they come from a different engine than BDRC and the human
# review surface needs both BDRC attempts and the vision read side-by-side.
VISION_TRANSCRIPT_FILE = "vision_ocr.json"
VISION_QUALITY_FILE = "vision_quality.json"

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
    """All persisted state for one page of a job.

    ``vision_transcript`` / ``vision_quality`` are populated when the T-07
    Claude vision-OCR fallback ran on this page; they sit next to the BDRC
    attempts list rather than inside it so the human review UI can show both
    engines' reads side-by-side. Both are ``None`` on pages where vision was
    never consulted (the common case — most pages accept on first OCR).
    """
    index: int
    image_path: Path
    settings: dict[str, Any]
    attempts: list[AttemptRecord] = field(default_factory=list)
    final_text: str | None = None
    final_quality: dict[str, Any] | None = None
    notes: str | None = None
    vision_transcript: dict[str, Any] | None = None
    vision_quality: dict[str, Any] | None = None


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

    The job directory is created with ``exist_ok=False``, so a generated
    ``job_id`` that happens to collide with an existing job (or an explicit
    ``job_id`` that's already taken) raises ``FileExistsError`` rather than
    clobbering data — callers should catch it and retry with a fresh id.
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
    manifest = json.loads((job_dir / MANIFEST_FILE).read_text(encoding="utf-8"))
    baseline = json.loads((job_dir / BASELINE_SETTINGS_FILE).read_text(encoding="utf-8"))
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

    settings = json.loads((page_dir / PAGE_SETTINGS_FILE).read_text(encoding="utf-8"))
    attempts_dir = page_dir / ATTEMPTS_DIR
    attempts = _load_attempts(attempts_dir) if attempts_dir.is_dir() else []

    final_text_path = page_dir / FINAL_TEXT_FILE
    final_text = (
        final_text_path.read_text(encoding="utf-8") if final_text_path.is_file() else None
    )

    final_quality_path = page_dir / FINAL_QUALITY_FILE
    final_quality = (
        json.loads(final_quality_path.read_text(encoding="utf-8"))
        if final_quality_path.is_file()
        else None
    )

    notes_path = page_dir / NOTES_FILE
    notes = notes_path.read_text(encoding="utf-8") if notes_path.is_file() else None

    vision_transcript_path = page_dir / VISION_TRANSCRIPT_FILE
    vision_transcript = (
        json.loads(vision_transcript_path.read_text(encoding="utf-8"))
        if vision_transcript_path.is_file()
        else None
    )

    vision_quality_path = page_dir / VISION_QUALITY_FILE
    vision_quality = (
        json.loads(vision_quality_path.read_text(encoding="utf-8"))
        if vision_quality_path.is_file()
        else None
    )

    return PageState(
        index=page_index,
        image_path=page_dir / PAGE_IMAGE_FILE,
        settings=settings,
        attempts=attempts,
        final_text=final_text,
        final_quality=final_quality,
        notes=notes,
        vision_transcript=vision_transcript,
        vision_quality=vision_quality,
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


def save_attempt_verdict(
    job: Job,
    page_index: int,
    verdict: dict[str, Any],
) -> None:
    """Attach an AI verdict to the most recently saved attempt on a page.

    Called after ``save_page_attempt`` (which writes OCR text + quality) once
    the diagnostician has returned. Writes ``ai_verdict.json`` under the
    highest-numbered ``attempts/NN/`` directory — raises ``FileNotFoundError``
    if no attempt has been saved yet, because a verdict has no meaning without
    one.
    """
    attempts_dir = job.root / _page_dir_name(page_index) / ATTEMPTS_DIR
    candidates = [
        p for p in attempts_dir.iterdir() if p.is_dir() and p.name.isdigit()
    ] if attempts_dir.is_dir() else []
    if not candidates:
        raise FileNotFoundError(
            f"No attempts to attach a verdict to under {attempts_dir}"
        )
    latest = max(candidates, key=lambda p: int(p.name))
    _atomic_write_json(latest / ATTEMPT_VERDICT_FILE, verdict)


def save_vision_transcript(
    job: Job,
    page_index: int,
    *,
    transcript: dict[str, Any],
    quality: dict[str, Any] | None = None,
) -> None:
    """Persist a T-07 vision-OCR transcript + its quality next to the page.

    Distinct from ``save_page_attempt`` because vision results come from a
    different engine than the BDRC attempts; storing them at the page level
    (not under ``attempts/NN/``) keeps the BDRC retry log semantically clean
    and gives the review UI a single well-known path for the fallback read.

    ``transcript`` is the serialized ``VisionTranscript`` (text + optional
    notes). ``quality`` follows the same shape ``save_page_attempt`` writes
    for BDRC attempts so the UI can render either with the same code.
    """
    page_dir = job.root / _page_dir_name(page_index)
    if not page_dir.is_dir():
        raise FileNotFoundError(f"No page directory: {page_dir}")
    _atomic_write_json(page_dir / VISION_TRANSCRIPT_FILE, transcript)
    if quality is not None:
        _atomic_write_json(page_dir / VISION_QUALITY_FILE, quality)


def update_page_settings(
    job: Job,
    page_index: int,
    settings: dict[str, Any],
) -> None:
    """Overwrite the page's ``settings.json`` with ``settings``.

    Retries mutate the page's copy of settings, not the job baseline (per the
    plan's per-page settings model). Pass the full settings dict — callers do
    their own merge with the prior value and persist the result.
    """
    page_dir = job.root / _page_dir_name(page_index)
    if not page_dir.is_dir():
        raise FileNotFoundError(f"No page directory: {page_dir}")
    _atomic_write_json(page_dir / PAGE_SETTINGS_FILE, dict(settings))


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
        except (json.JSONDecodeError, KeyError, OSError):
            # Malformed manifest, missing key, or a job that was deleted
            # between the is_file() check above and the read — skip it.
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
                ocr_text=ocr_path.read_text(encoding="utf-8") if ocr_path.is_file() else "",
                quality=(
                    json.loads(quality_path.read_text(encoding="utf-8"))
                    if quality_path.is_file()
                    else None
                ),
                ai_verdict=(
                    json.loads(verdict_path.read_text(encoding="utf-8"))
                    if verdict_path.is_file()
                    else None
                ),
            )
        )
    return records


def _atomic_write_text(path: Path, content: str) -> None:
    """Write ``content`` to ``path`` atomically and durably as UTF-8.

    Content goes to a uniquely-named temp file in the same directory (so
    two writers never share a temp path), which is flushed and ``fsync``'d
    before being ``os.replace``'d into place; the parent directory is then
    ``fsync``'d so the rename itself survives a crash. If anything fails
    before the replace, the temp file is removed rather than orphaned.
    """
    fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=path.name + ".", suffix=".tmp"
    )
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise

    # Best-effort directory fsync so the rename is durable. Not all
    # platforms allow opening/fsync'ing a directory (e.g. Windows), and the
    # data fsync above is the part that matters for not losing contents.
    try:
        dir_fd = os.open(str(path.parent), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(dir_fd)
    except OSError:
        pass
    finally:
        os.close(dir_fd)


def _atomic_write_json(path: Path, obj: Any) -> None:
    _atomic_write_text(
        path, json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False)
    )


def _render_pdf(pdf_bytes: bytes, *, dpi: int) -> Sequence:
    """Render a PDF to PIL images. Pulled out for monkeypatching in tests.

    Returns a sequence of page images; callers (and test fakes) only rely
    on each element supporting ``.save(path, "PNG")`` — i.e. the Pillow
    ``Image`` protocol — so a fake can return any object with that method.
    """
    from pdf2image import convert_from_bytes
    return convert_from_bytes(pdf_bytes, dpi=dpi)
