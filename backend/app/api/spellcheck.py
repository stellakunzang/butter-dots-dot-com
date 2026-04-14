"""
Spell check API endpoints — text and PDF upload.
"""
import json
import logging
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.schemas.spellcheck import (
    ErrorResponse,
    JobStatusResponse,
    PDFErrorResponse,
    PDFUploadAsyncResponse,
    PDFUploadSyncResponse,
    SpellCheckRequest,
    SpellCheckResponse,
)
from app.spellcheck.engine import TibetanSpellChecker

logger = logging.getLogger(__name__)

router = APIRouter()


RESULTS_DIR = Path(__file__).parent.parent.parent / "results"
UPLOADS_DIR = Path(__file__).parent.parent.parent / "uploads"
RESULTS_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Text spell check (existing endpoint — unchanged)
# ---------------------------------------------------------------------------

@router.post("/spellcheck/text", response_model=SpellCheckResponse)
async def check_text(request: SpellCheckRequest):
    """
    Check Tibetan text for spelling errors.

    Returns a list of errors with their positions, types, and severity levels.
    Uses grammatical rules to validate:
    - Prefix combinations
    - Superscript combinations
    - Suffix validity
    - Post-suffix validity
    - Syllable structure
    """
    try:
        checker = TibetanSpellChecker()
        raw_errors = checker.check_text(request.text)

        errors = [
            ErrorResponse(
                word=error.get("word", ""),
                position=error.get("position", 0),
                error_type=error.get("error_type", "unknown"),
                severity=error.get("severity", "error"),
                message=error.get("message"),
                component=error.get("component"),
                corpus_hit=error.get("corpus_hit"),
            )
            for error in raw_errors
        ]

        _log_spellcheck_result(
            source="text",
            text_length=len(request.text),
            errors=raw_errors,
        )

        return SpellCheckResponse(
            text=request.text,
            error_count=len(errors),
            errors=errors,
        )

    except Exception as e:
        logger.exception("Error processing spell check")
        raise HTTPException(status_code=500, detail=f"Error processing spell check: {e}")


# ---------------------------------------------------------------------------
# PDF upload
# ---------------------------------------------------------------------------

@router.post("/spellcheck/upload")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    email: str = Form(None),
):
    """
    Upload a PDF for OCR and spell checking.

    - PDFs ≤ 15 pages: processed synchronously, returns results immediately.
    - PDFs > 15 pages: queued for async processing; returns job_id for polling.
      Provide an email address to receive a notification when complete.

    Returns either PDFUploadSyncResponse or PDFUploadAsyncResponse.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    # Quick page count check before committing to full processing
    try:
        import pdfplumber
        import io as _io

        with pdfplumber.open(_io.BytesIO(pdf_bytes)) as _pdf:
            page_count = len(_pdf.pages)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not read PDF: {e}")

    return await _process_sync(pdf_bytes, file.filename, page_count)


async def _process_sync(pdf_bytes: bytes, filename: str, page_count: int):
    """Process a small PDF synchronously and return all results."""
    from app import jobs as job_store
    from app.pdf.extractor import extract_pdf
    from app.pdf.annotator import annotate_pdf
    from app.pdf.docx_exporter import build_docx

    job = job_store.create_job(filename, page_count)

    try:
        pages, is_scanned = extract_pdf(pdf_bytes)
        errors_by_page, all_errors = _run_spellcheck(pages)

        annotated_pdf = annotate_pdf(pdf_bytes, pages, errors_by_page)
        docx_bytes = build_docx(pages, errors_by_page, filename)

        pdf_path = RESULTS_DIR / f"{job.id}.pdf"
        docx_path = RESULTS_DIR / f"{job.id}.docx"
        pdf_path.write_bytes(annotated_pdf)
        docx_path.write_bytes(docx_bytes)

        job_store.mark_completed(job.id, pdf_path, docx_path, all_errors)

        _log_spellcheck_result(
            source="pdf",
            text_length=sum(len(p.text) for p in pages),
            errors=all_errors,
        )

        return PDFUploadSyncResponse(
            job_id=job.id,
            page_count=page_count,
            error_count=len(all_errors),
            errors=[PDFErrorResponse(**e) for e in all_errors],
            is_scanned=is_scanned,
            pdf_url=f"/api/v1/spellcheck/result/{job.id}/pdf",
            docx_url=f"/api/v1/spellcheck/result/{job.id}/docx",
        )

    except Exception as e:
        job_store.mark_failed(job.id, str(e))
        logger.exception("Sync PDF processing failed for job %s", job.id)
        raise HTTPException(status_code=500, detail=f"PDF processing failed: {e}")


# TODO: Page limit + async flow is temporarily disabled (removed the SYNC_PAGE_LIMIT check
# in upload_pdf). The infrastructure below (_queue_async_job, _background_process, the
# email param on the upload endpoint, and the job-status polling endpoints) is all still
# wired up. Once we have user feedback on whether async delivery is wanted, either:
#   - Re-add the limit (e.g. SYNC_PAGE_LIMIT = 15) and restore the routing logic, or
#   - Delete _queue_async_job, _background_process, the email Form param, BackgroundTasks,
#     and the /spellcheck/job/* endpoints entirely.
async def _queue_async_job(
    pdf_bytes: bytes,
    filename: str,
    page_count: int,
    email: str,
    background_tasks: BackgroundTasks,
):
    """Queue a large PDF for background processing."""
    from app import jobs as job_store

    job = job_store.create_job(filename, page_count, email=email)

    # Save upload for background task
    upload_path = UPLOADS_DIR / f"{job.id}.pdf"
    upload_path.write_bytes(pdf_bytes)

    background_tasks.add_task(_background_process, job.id, upload_path, filename, email)

    return PDFUploadAsyncResponse(
        job_id=job.id,
        page_count=page_count,
        status="pending",
        message=(
            f"Your {page_count}-page PDF has been queued. "
            f"Results will be sent to {email} when complete. "
            f"You can also poll GET /api/v1/spellcheck/job/{job.id} for status."
        ),
    )


def _background_process(job_id: str, upload_path: Path, filename: str, email: str) -> None:
    """Background task: process a large PDF and send email when done."""
    import asyncio
    from app import jobs as job_store
    from app.pdf.extractor import extract_pdf
    from app.pdf.annotator import annotate_pdf
    from app.pdf.docx_exporter import build_docx
    from app.utils.email import send_results_email

    job_store.update_job(job_id, status=job_store.JobStatus.PROCESSING, progress=5)

    try:
        pdf_bytes = upload_path.read_bytes()

        job_store.update_job(job_id, progress=10)
        pages, is_scanned = extract_pdf(pdf_bytes)

        job_store.update_job(job_id, progress=60)
        errors_by_page, all_errors = _run_spellcheck(pages)

        job_store.update_job(job_id, progress=75)
        annotated_pdf = annotate_pdf(pdf_bytes, pages, errors_by_page)
        docx_bytes = build_docx(pages, errors_by_page, filename)

        pdf_path = RESULTS_DIR / f"{job_id}.pdf"
        docx_path = RESULTS_DIR / f"{job_id}.docx"
        pdf_path.write_bytes(annotated_pdf)
        docx_path.write_bytes(docx_bytes)

        job_store.mark_completed(job_id, pdf_path, docx_path, all_errors)

        # Send email notification (async stub — run in new event loop)
        from app.config import settings
        download_url = f"{settings.public_base_url}/api/v1/spellcheck/result/{job_id}/pdf"
        asyncio.run(send_results_email(to=email, job_id=job_id, download_url=download_url))

    except Exception as e:
        job_store.mark_failed(job_id, str(e))
        logger.exception("Background processing failed for job %s", job_id)
    finally:
        # Clean up upload
        try:
            upload_path.unlink(missing_ok=True)
        except Exception:
            pass


def _log_spellcheck_result(source: str, text_length: int, errors: list[dict]) -> None:
    """
    Emit a structured log line for every spell check result.

    Each line starts with 'spellcheck_result' so it can be isolated with:
        grep spellcheck_result <logfile>
        grep spellcheck_result <logfile> | jq '.corpus_hits'

    Fields:
        source        — "text" or "pdf"
        text_length   — character count of input
        error_count   — total errors returned
        phase1_errors — structural errors (severity != warning and != info)
        unknown_words — syllables flagged by Phase 2 dictionary lookup
        corpus_hits   — Phase 1 errors where the syllable WAS in the corpus
                        (potential false positives; key metric for tuning)
        dict_active   — whether the dictionary was loaded for this check
    """
    phase1 = [e for e in errors if e.get("severity") not in ("warning", "info")]
    unknown = [e for e in errors if e.get("error_type") == "unknown_word"]
    corpus_hits = [e for e in phase1 if e.get("corpus_hit") is True]
    dict_active = any(e.get("corpus_hit") is not None for e in errors)

    logger.info(
        "spellcheck_result %s",
        json.dumps({
            "source": source,
            "text_length": text_length,
            "error_count": len(errors),
            "phase1_errors": len(phase1),
            "unknown_words": len(unknown),
            "corpus_hits": len(corpus_hits),
            "dict_active": dict_active,
        }),
    )


def _run_spellcheck(pages) -> tuple[dict[int, list[str]], list[dict]]:
    """
    Run the spell checker over all extracted page text.

    Returns:
        errors_by_page: dict mapping page_number → list of error word strings
        all_errors: flat list of error dicts (serialisable for JSON output)
    """
    checker = TibetanSpellChecker()
    errors_by_page: dict[int, list[str]] = {}
    all_errors: list[dict] = []

    for page in pages:
        if not page.text.strip():
            continue

        raw_errors = checker.check_text(page.text)

        page_error_words = [e.get("word", "") for e in raw_errors if e.get("word")]
        if page_error_words:
            errors_by_page[page.page_number] = page_error_words

        for e in raw_errors:
            all_errors.append(
                {
                    "word": e.get("word", ""),
                    "page": page.page_number,
                    "error_type": e.get("error_type", "unknown"),
                    "severity": e.get("severity", "error"),
                    "message": e.get("message"),
                    "component": e.get("component"),
                    "corpus_hit": e.get("corpus_hit"),
                }
            )

    return errors_by_page, all_errors


# ---------------------------------------------------------------------------
# Job status polling
# ---------------------------------------------------------------------------

@router.get("/spellcheck/job/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Poll the status of an async PDF processing job."""
    from app import jobs as job_store

    job = job_store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    response = JobStatusResponse(
        job_id=job.id,
        status=job.status.value,
        progress=job.progress,
        page_count=job.page_count,
        error_count=len(job.errors) if job.errors is not None else None,
        error_message=job.error_message,
    )

    if job.status == job_store.JobStatus.COMPLETED:
        response.pdf_url = f"/api/v1/spellcheck/result/{job_id}/pdf"
        response.docx_url = f"/api/v1/spellcheck/result/{job_id}/docx"

    return response


# ---------------------------------------------------------------------------
# Result downloads
# ---------------------------------------------------------------------------

@router.get("/spellcheck/result/{job_id}/pdf")
async def download_pdf(job_id: str):
    """Download the annotated PDF for a completed job."""
    job = _get_completed_job(job_id)
    if not job.pdf_result_path or not job.pdf_result_path.exists():
        raise HTTPException(status_code=404, detail="PDF result not found")
    return FileResponse(
        path=str(job.pdf_result_path),
        media_type="application/pdf",
        filename=f"spellcheck_{job.original_filename}",
    )


@router.get("/spellcheck/result/{job_id}/docx")
async def download_docx(job_id: str):
    """Download the editable Word document for a completed job."""
    job = _get_completed_job(job_id)
    if not job.docx_result_path or not job.docx_result_path.exists():
        raise HTTPException(status_code=404, detail="DOCX result not found")
    stem = Path(job.original_filename).stem
    return FileResponse(
        path=str(job.docx_result_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"spellcheck_{stem}.docx",
    )


def _get_completed_job(job_id: str):
    from app import jobs as job_store

    job = job_store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    if job.status != job_store.JobStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail=f"Job is not yet complete (status: {job.status.value})",
        )
    return job
