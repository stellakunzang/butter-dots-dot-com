"""
In-memory job store for async PDF processing jobs.

The dict and the result files live in this process. The lock below is
in-process only, so run a single API instance. A second process would not
see these jobs and could delete another instance's result files.

Completed and failed jobs are removed after ``JOB_TTL``, and their result
files are deleted with them. Pending and processing jobs are left alone so
a long PDF is not swept out from under the background task.

``database/schema.sql`` keeps the ``jobs`` and ``spell_errors`` tables for
inspecting a completed job after this process is gone. This module does
not read or write them.
"""

import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

JOB_TTL = timedelta(hours=24)


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PDFJob:
    id: str
    original_filename: str
    email: Optional[str]
    page_count: int
    status: JobStatus = JobStatus.PENDING
    progress: int = 0  # 0–100
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    # Result file paths (relative to backend/results/)
    pdf_result_path: Optional[Path] = None
    docx_result_path: Optional[Path] = None

    # Structured errors (JSON-serialisable)
    errors: Optional[list[dict]] = None

    error_message: Optional[str] = None


_jobs: dict[str, PDFJob] = {}
_lock = threading.Lock()


def create_job(filename: str, page_count: int, email: Optional[str] = None) -> PDFJob:
    job_id = str(uuid.uuid4())
    job = PDFJob(id=job_id, original_filename=filename, email=email, page_count=page_count)
    with _lock:
        _sweep_locked()
        _jobs[job_id] = job
    logger.info("Created job %s (%s, %d pages)", job_id, filename, page_count)
    return job


def get_job(job_id: str) -> Optional[PDFJob]:
    with _lock:
        _sweep_locked()
        return _jobs.get(job_id)


def update_job(job_id: str, **kwargs) -> Optional[PDFJob]:
    with _lock:
        _sweep_locked()
        job = _jobs.get(job_id)
        if job is None:
            return None
        for key, value in kwargs.items():
            setattr(job, key, value)
        return job


def mark_completed(job_id: str, pdf_path: Path, docx_path: Path, errors: list[dict]) -> None:
    update_job(
        job_id,
        status=JobStatus.COMPLETED,
        progress=100,
        pdf_result_path=pdf_path,
        docx_result_path=docx_path,
        errors=errors,
        completed_at=datetime.now(timezone.utc),
    )
    logger.info("Job %s completed (%d errors)", job_id, len(errors))


def mark_failed(job_id: str, error_message: str) -> None:
    update_job(
        job_id,
        status=JobStatus.FAILED,
        error_message=error_message,
        completed_at=datetime.now(timezone.utc),
    )
    logger.error("Job %s failed: %s", job_id, error_message)


def _sweep_locked(now: datetime | None = None) -> None:
    """Drop finished jobs and old result files. Caller holds ``_lock``."""
    now = now or datetime.now(timezone.utc)
    cutoff = now - JOB_TTL
    expired = [
        job_id
        for job_id, job in _jobs.items()
        if job.status in (JobStatus.COMPLETED, JobStatus.FAILED)
        and _as_utc(job.created_at) < cutoff
    ]
    for job_id in expired:
        job = _jobs.pop(job_id)
        _unlink(job.pdf_result_path)
        _unlink(job.docx_result_path)
        logger.info("Expired job %s", job_id)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _unlink(path: Path | None) -> None:
    if path is None:
        return
    try:
        path.unlink(missing_ok=True)
    except OSError:
        logger.warning("Could not remove expired result %s", path)
