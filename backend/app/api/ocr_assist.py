"""
Local-only interactive OCR assist API.

Gated by ``OCR_ASSIST_LOCAL=true``. Bulk jobs are BDRC + quality scorer only;
AI vision compare is an explicit per-page action.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel


from app.config import settings
from app.ocr_assist.compare_vision import VisionCompareResult, compare_vision_providers
from app.ocr_assist.job_store import (
    OUTPUT_DOCX_FILE,
    Job,
    create_job,
    finalize_page,
    load_job,
    load_page,
    reset_page,
)
from app.ocr_assist.runner import run_all_pages, run_page

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ocr-assist", tags=["ocr-assist"])

MAX_UPLOAD_BYTES = 100 * 1024 * 1024  # 100 MB

# In-process run flags so the UI can show "running" while background BDRC works.
_running_jobs: set[str] = set()


class PageActionRequest(BaseModel):
    action: Literal[
        "accept",
        "edit_accept",
        "retry",
        "compare_vision",
        "accept_vision",
    ]
    text: str | None = None
    provider: Literal["anthropic", "gemini"] | None = None


def _jobs_root() -> Path:
    root = Path(settings.ocr_assist_jobs_root)
    if not root.is_absolute():
        root = Path(__file__).resolve().parent.parent.parent / root
    root.mkdir(parents=True, exist_ok=True)
    return root


def _require_job(job_id: str) -> Job:
    try:
        return load_job(_jobs_root(), job_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}") from exc


def _page_status(job: Job, page_index: int) -> str:
    page = load_page(job, page_index)
    if page.final_text is not None:
        return "final"
    if page.attempts:
        return "needs_review"
    return "pending"


def _serialize_job(job: Job) -> dict[str, Any]:
    pages = []
    for i in range(1, job.page_count + 1):
        page = load_page(job, i)
        latest = page.attempts[-1] if page.attempts else None
        pages.append(
            {
                "index": i,
                "status": _page_status(job, i),
                "attempt_count": len(page.attempts),
                "composite_score": (
                    (latest.quality or {}).get("composite_score") if latest else None
                ),
                "has_vision_compare": bool(page.vision_by_provider),
            }
        )
    return {
        "id": job.id,
        "source_file": job.source_file,
        "page_count": job.page_count,
        "status": job.status,
        "running": job.id in _running_jobs,
        "created_at": job.created_at.isoformat(),
        "pages": pages,
        "docx_ready": (job.root / OUTPUT_DOCX_FILE).is_file(),
    }


def _serialize_page(job: Job, page_index: int) -> dict[str, Any]:
    page = load_page(job, page_index)
    latest = page.attempts[-1] if page.attempts else None
    return {
        "index": page.index,
        "status": _page_status(job, page_index),
        "settings": page.settings,
        "final_text": page.final_text,
        "final_quality": page.final_quality,
        "notes": page.notes,
        "latest_ocr_text": latest.ocr_text if latest else None,
        "latest_quality": latest.quality if latest else None,
        "attempts": [
            {
                "number": a.number,
                "ocr_text": a.ocr_text,
                "quality": a.quality,
                "ai_verdict": a.ai_verdict,
            }
            for a in page.attempts
        ],
        "vision_legacy": {
            "transcript": page.vision_transcript,
            "quality": page.vision_quality,
        },
        "vision_by_provider": page.vision_by_provider,
        "image_url": f"/api/v1/ocr-assist/jobs/{job.id}/pages/{page_index}/image",
    }


def _run_job_bdrc_only(job_id: str) -> None:
    _running_jobs.add(job_id)
    try:
        job = load_job(_jobs_root(), job_id)
        run_all_pages(job)  # no diagnostician / vision
    except Exception:
        logger.exception("ocr-assist background run failed for job %s", job_id)
    finally:
        _running_jobs.discard(job_id)


@router.post("/jobs")
async def create_ocr_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """Upload a PDF and start a BDRC-only job (no bulk AI)."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Upload a .pdf file")
    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Empty upload")
    if len(pdf_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="PDF exceeds size limit")

    job = await asyncio.to_thread(
        create_job,
        pdf_bytes,
        source_file=file.filename,
        baseline_settings={"model_variant": settings.ocr_model_name},
        jobs_root=_jobs_root(),
    )
    background_tasks.add_task(_run_job_bdrc_only, job.id)
    return _serialize_job(job)


@router.get("/jobs/{job_id}")
async def get_ocr_job(job_id: str):
    return _serialize_job(_require_job(job_id))


@router.get("/jobs/{job_id}/pages/{page_index}")
async def get_ocr_page(job_id: str, page_index: int):
    job = _require_job(job_id)
    if page_index < 1 or page_index > job.page_count:
        raise HTTPException(status_code=404, detail="Page out of range")
    return _serialize_page(job, page_index)


@router.get("/jobs/{job_id}/pages/{page_index}/image")
async def get_ocr_page_image(job_id: str, page_index: int):
    job = _require_job(job_id)
    page = load_page(job, page_index)
    if not page.image_path.is_file():
        raise HTTPException(status_code=404, detail="Page image missing")
    return FileResponse(page.image_path, media_type="image/png")


@router.get("/jobs/{job_id}/docx")
async def download_ocr_docx(job_id: str):
    job = _require_job(job_id)
    path = job.root / OUTPUT_DOCX_FILE
    if not path.is_file():
        raise HTTPException(status_code=404, detail="DOCX not ready (no finalized pages yet)")
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"{job.id}.docx",
    )


@router.post("/jobs/{job_id}/pages/{page_index}/action")
async def page_action(job_id: str, page_index: int, body: PageActionRequest):
    job = _require_job(job_id)
    if page_index < 1 or page_index > job.page_count:
        raise HTTPException(status_code=404, detail="Page out of range")

    if body.action == "accept":
        return await asyncio.to_thread(_action_accept, job, page_index, body.text)
    if body.action == "edit_accept":
        if body.text is None:
            raise HTTPException(status_code=400, detail="text is required for edit_accept")
        return await asyncio.to_thread(_action_accept, job, page_index, body.text)
    if body.action == "retry":
        return await asyncio.to_thread(_action_retry, job, page_index)
    if body.action == "compare_vision":
        compare = await asyncio.to_thread(compare_vision_providers, job, page_index)
        return {
            "page": _serialize_page(job, page_index),
            "compare": _serialize_compare(compare),
        }
    if body.action == "accept_vision":
        if not body.provider and body.text is None:
            raise HTTPException(
                status_code=400,
                detail="provider or text is required for accept_vision",
            )
        return await asyncio.to_thread(
            _action_accept_vision, job, page_index, body.provider, body.text
        )
    raise HTTPException(status_code=400, detail=f"Unknown action: {body.action}")


def _serialize_compare(compare: VisionCompareResult) -> dict[str, Any]:
    return {
        "page_index": compare.page_index,
        "results": [
            {
                "provider": r.provider,
                "transcript": r.transcript,
                "quality": r.quality,
                "composite_score": r.composite_score,
                "decision": r.decision,
                "error": r.error,
            }
            for r in compare.results
        ],
    }


def _action_accept(job: Job, page_index: int, text: str | None) -> dict[str, Any]:
    page = load_page(job, page_index)
    if text is None:
        if page.attempts:
            text = page.attempts[-1].ocr_text
        elif page.final_text is not None:
            text = page.final_text
        else:
            raise HTTPException(status_code=400, detail="No OCR text to accept")
    quality = page.attempts[-1].quality if page.attempts else page.final_quality
    finalize_page(
        job,
        page_index,
        final_text=text,
        final_quality=quality,
        notes="accepted via ocr-assist UI",
    )
    return _serialize_page(job, page_index)


def _action_retry(job: Job, page_index: int) -> dict[str, Any]:
    reset_page(job, page_index)  # keeps attempts/settings by default
    run_page(job, page_index)  # BDRC only
    return _serialize_page(job, page_index)


def _action_accept_vision(
    job: Job,
    page_index: int,
    provider: str | None,
    text: str | None,
) -> dict[str, Any]:
    page = load_page(job, page_index)
    notes = "accepted via vision compare"
    quality = None
    if text is None:
        if not provider:
            raise HTTPException(status_code=400, detail="provider required when text omitted")
        entry = page.vision_by_provider.get(provider)
        if not entry or not entry.get("transcript"):
            raise HTTPException(
                status_code=400,
                detail=f"No vision transcript for provider {provider!r}; run compare_vision first",
            )
        text = entry["transcript"].get("text") or ""
        quality = entry.get("quality")
        notes = f"accepted via vision compare ({provider})"
    elif provider:
        notes = f"accepted via vision compare ({provider}, edited)"
        entry = page.vision_by_provider.get(provider) or {}
        quality = entry.get("quality")

    finalize_page(
        job,
        page_index,
        final_text=text,
        final_quality=quality,
        notes=notes,
    )
    return _serialize_page(job, page_index)
