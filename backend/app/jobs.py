"""
In-memory job store for async PDF processing jobs.

Simple dict-backed store keyed by UUID. Suitable for single-instance MVP.
Jobs don't survive restarts — acceptable at this stage.

Future: replace with a DB-backed store (SQLAlchemy model) when persistence
or multi-instance deployment is needed.
"""
import uuid
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


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
    progress: int = 0          # 0–100
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    # Result file paths (relative to backend/results/)
    pdf_result_path: Optional[Path] = None
    docx_result_path: Optional[Path] = None

    # Structured errors (JSON-serialisable)
    errors: Optional[list[dict]] = None

    error_message: Optional[str] = None


# Module-level store
_jobs: dict[str, PDFJob] = {}


def create_job(filename: str, page_count: int, email: Optional[str] = None) -> PDFJob:
    job_id = str(uuid.uuid4())
    job = PDFJob(id=job_id, original_filename=filename, email=email, page_count=page_count)
    _jobs[job_id] = job
    logger.info("Created job %s (%s, %d pages)", job_id, filename, page_count)
    return job


def get_job(job_id: str) -> Optional[PDFJob]:
    return _jobs.get(job_id)


def update_job(job_id: str, **kwargs) -> Optional[PDFJob]:
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
