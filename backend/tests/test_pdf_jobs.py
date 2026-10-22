"""In-memory PDF job store: expiry and the result-email failure path."""

from datetime import datetime, timedelta, timezone

import pytest


@pytest.fixture
def jobs(monkeypatch):
    from app import jobs as job_store

    monkeypatch.setattr(job_store, "_jobs", {})
    return job_store


def test_finished_job_and_its_files_expire(jobs, tmp_path):
    job = jobs.create_job("leaf.pdf", page_count=2)
    pdf = tmp_path / "out.pdf"
    docx = tmp_path / "out.docx"
    pdf.write_bytes(b"pdf")
    docx.write_bytes(b"docx")
    jobs.mark_completed(job.id, pdf, docx, [])
    job.completed_at = datetime.now(timezone.utc) - jobs.JOB_TTL - timedelta(minutes=1)

    assert jobs.get_job(job.id) is None
    assert not pdf.exists()
    assert not docx.exists()


def test_pending_job_is_not_expired(jobs):
    job = jobs.create_job("leaf.pdf", page_count=2)
    job.created_at = datetime.now(timezone.utc) - jobs.JOB_TTL - timedelta(hours=1)

    stored = jobs.get_job(job.id)
    assert stored is not None
    assert stored.status == jobs.JobStatus.PENDING


def test_email_failure_leaves_the_job_completed(jobs, tmp_path, monkeypatch):
    from app.api import spellcheck

    monkeypatch.setattr(spellcheck, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(spellcheck, "_run_spellcheck", lambda pages: ({}, []))
    monkeypatch.setattr("app.pdf.extractor.extract_pdf", lambda data: ([], False))
    monkeypatch.setattr("app.pdf.annotator.annotate_pdf", lambda *args, **kwargs: b"%PDF")
    monkeypatch.setattr("app.pdf.docx_exporter.build_docx", lambda *args, **kwargs: b"docx")

    async def boom(**kwargs):
        raise RuntimeError("smtp down")

    monkeypatch.setattr("app.utils.email.send_results_email", boom)

    job = jobs.create_job("leaf.pdf", page_count=20, email="a@example.com")
    upload = tmp_path / "in.pdf"
    upload.write_bytes(b"%PDF")

    spellcheck._background_process(job.id, upload, "leaf.pdf", "a@example.com")

    stored = jobs.get_job(job.id)
    assert stored is not None
    assert stored.status == jobs.JobStatus.COMPLETED
    assert (tmp_path / f"{job.id}.pdf").is_file()
