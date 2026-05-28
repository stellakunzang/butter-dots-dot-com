"""
Tests for the OCR-assist job store.

Covers the A/C from T-04:
- create_job persists manifest, baseline_settings, and one page dir per page
- save_page_attempt writes under attempts/NN/ with monotonic numbering
- finalize_page writes final.txt + final_quality.json
- load_job round-trips a previously saved job
- list_jobs round-trips
- Atomic writes leave no orphaned .tmp file on success
"""
from datetime import datetime
from pathlib import Path

import pytest
from PIL import Image

from app.ocr_assist import job_store
from app.ocr_assist.job_store import (
    BASELINE_SETTINGS_FILE,
    FINAL_QUALITY_FILE,
    FINAL_TEXT_FILE,
    JOB_STATUS_IN_PROGRESS,
    MANIFEST_FILE,
    PAGE_IMAGE_FILE,
    create_job,
    finalize_page,
    list_jobs,
    load_job,
    load_page,
    save_page_attempt,
)


@pytest.fixture
def fake_pdf(monkeypatch):
    """Bypass pdf2image: hand create_job a small list of in-memory PIL images.

    pdf2image needs poppler on the system. Mocking the render keeps this
    test suite self-contained and fast.
    """
    def _fake_render(pdf_bytes: bytes, *, dpi: int):
        return [Image.new("RGB", (40, 40), "white") for _ in range(3)]

    monkeypatch.setattr(job_store, "_render_pdf", _fake_render)
    return b"fake-pdf-bytes"


@pytest.fixture
def baseline_settings() -> dict:
    return {"k_factor": 2.0, "model_variant": "Modern", "rotate": 0}


@pytest.fixture
def created_job(tmp_path: Path, fake_pdf, baseline_settings) -> "tuple[Path, str]":
    job = create_job(
        fake_pdf,
        source_file="sample.pdf",
        baseline_settings=baseline_settings,
        jobs_root=tmp_path,
    )
    return tmp_path, job.id


class TestCreateJob:
    def test_persists_manifest_and_baseline(self, tmp_path, fake_pdf, baseline_settings):
        job = create_job(
            fake_pdf,
            source_file="sample.pdf",
            baseline_settings=baseline_settings,
            jobs_root=tmp_path,
        )
        assert (job.root / MANIFEST_FILE).is_file()
        assert (job.root / BASELINE_SETTINGS_FILE).is_file()
        assert job.page_count == 3
        assert job.status == JOB_STATUS_IN_PROGRESS
        assert isinstance(job.created_at, datetime)
        assert job.baseline_settings == baseline_settings

    def test_persists_page_dirs_with_image_and_settings(self, tmp_path, fake_pdf, baseline_settings):
        job = create_job(
            fake_pdf,
            source_file="sample.pdf",
            baseline_settings=baseline_settings,
            jobs_root=tmp_path,
        )
        for i in range(1, 4):
            page_dir = job.root / f"page-{i:03d}"
            assert page_dir.is_dir()
            assert (page_dir / PAGE_IMAGE_FILE).is_file()
            assert (page_dir / "settings.json").is_file()
            assert (page_dir / "attempts").is_dir()

    def test_page_settings_start_as_baseline_copy(self, tmp_path, fake_pdf, baseline_settings):
        job = create_job(
            fake_pdf,
            source_file="sample.pdf",
            baseline_settings=baseline_settings,
            jobs_root=tmp_path,
        )
        page = load_page(job, 1)
        assert page.settings == baseline_settings
        # Mutating the returned dict must not affect job.baseline_settings —
        # they're independent copies.
        page.settings["k_factor"] = 999
        assert job.baseline_settings["k_factor"] == 2.0

    def test_refuses_to_clobber_existing_job(self, tmp_path, fake_pdf, baseline_settings):
        create_job(
            fake_pdf,
            source_file="sample.pdf",
            baseline_settings=baseline_settings,
            jobs_root=tmp_path,
            job_id="fixed-id",
        )
        with pytest.raises(FileExistsError):
            create_job(
                fake_pdf,
                source_file="sample.pdf",
                baseline_settings=baseline_settings,
                jobs_root=tmp_path,
                job_id="fixed-id",
            )


class TestSavePageAttempt:
    def test_monotonic_numbering(self, created_job):
        jobs_root, job_id = created_job
        job = load_job(jobs_root, job_id)

        first = save_page_attempt(job, 1, ocr_text="first try", quality={"composite_score": 0.6})
        second = save_page_attempt(job, 1, ocr_text="second try", quality={"composite_score": 0.8})
        third = save_page_attempt(job, 1, ocr_text="third try")

        assert [first.number, second.number, third.number] == [1, 2, 3]
        for n in (1, 2, 3):
            assert (job.root / "page-001" / "attempts" / f"{n:02d}" / "ocr.txt").is_file()

    def test_attempts_load_back_in_order(self, created_job):
        jobs_root, job_id = created_job
        job = load_job(jobs_root, job_id)
        save_page_attempt(job, 1, ocr_text="A", quality={"composite_score": 0.6})
        save_page_attempt(job, 1, ocr_text="B", ai_verdict={"verdict": "retry"})

        page = load_page(job, 1)
        assert [a.number for a in page.attempts] == [1, 2]
        assert page.attempts[0].ocr_text == "A"
        assert page.attempts[0].quality == {"composite_score": 0.6}
        assert page.attempts[1].ocr_text == "B"
        assert page.attempts[1].ai_verdict == {"verdict": "retry"}

    def test_missing_page_dir_raises(self, created_job):
        jobs_root, job_id = created_job
        job = load_job(jobs_root, job_id)
        with pytest.raises(FileNotFoundError):
            save_page_attempt(job, 999, ocr_text="x")


class TestFinalizePage:
    def test_writes_final_text_and_quality(self, created_job):
        jobs_root, job_id = created_job
        job = load_job(jobs_root, job_id)

        page = finalize_page(
            job,
            2,
            final_text="བཀྲ་ཤིས།",
            final_quality={"composite_score": 0.92},
            notes="reviewed by human",
        )

        page_dir = job.root / "page-002"
        assert (page_dir / FINAL_TEXT_FILE).read_text() == "བཀྲ་ཤིས།"
        assert (page_dir / FINAL_QUALITY_FILE).is_file()
        assert (page_dir / "notes.md").read_text() == "reviewed by human"
        assert page.final_text == "བཀྲ་ཤིས།"
        assert page.final_quality == {"composite_score": 0.92}
        assert page.notes == "reviewed by human"


class TestLoadJobRoundTrip:
    def test_round_trips_metadata(self, created_job, baseline_settings):
        jobs_root, job_id = created_job
        job = load_job(jobs_root, job_id)
        assert job.id == job_id
        assert job.source_file == "sample.pdf"
        assert job.page_count == 3
        assert job.status == JOB_STATUS_IN_PROGRESS
        assert job.baseline_settings == baseline_settings

    def test_round_trips_page_with_attempts_and_final(self, created_job):
        jobs_root, job_id = created_job
        job = load_job(jobs_root, job_id)
        save_page_attempt(job, 1, ocr_text="attempt one", quality={"composite_score": 0.7})
        save_page_attempt(job, 1, ocr_text="attempt two")
        finalize_page(job, 1, final_text="final text", final_quality={"composite_score": 0.95})

        reloaded = load_job(jobs_root, job_id)
        page = load_page(reloaded, 1)
        assert len(page.attempts) == 2
        assert page.attempts[0].ocr_text == "attempt one"
        assert page.final_text == "final text"
        assert page.final_quality == {"composite_score": 0.95}

    def test_missing_job_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_job(tmp_path, "nope")


class TestListJobs:
    def test_returns_all_jobs(self, tmp_path, fake_pdf, baseline_settings):
        ids = [
            create_job(fake_pdf, "a.pdf", baseline_settings, tmp_path).id,
            create_job(fake_pdf, "b.pdf", baseline_settings, tmp_path).id,
        ]
        listed = list_jobs(tmp_path)
        assert sorted(j.id for j in listed) == sorted(ids)

    def test_empty_root_returns_empty_list(self, tmp_path):
        assert list_jobs(tmp_path / "does-not-exist") == []

    def test_skips_unrelated_directories(self, tmp_path, fake_pdf, baseline_settings):
        create_job(fake_pdf, "a.pdf", baseline_settings, tmp_path)
        (tmp_path / "not-a-job").mkdir()
        (tmp_path / "stray.txt").write_text("ignored")
        assert len(list_jobs(tmp_path)) == 1


class TestAtomicWrites:
    def test_no_orphan_tmp_files_after_create(self, created_job):
        jobs_root, job_id = created_job
        stray = [p for p in (jobs_root / job_id).rglob("*.tmp")]
        assert stray == []

    def test_no_orphan_tmp_files_after_attempt_and_finalize(self, created_job):
        jobs_root, job_id = created_job
        job = load_job(jobs_root, job_id)
        save_page_attempt(job, 1, ocr_text="x", quality={"composite_score": 0.5})
        finalize_page(job, 1, final_text="y", final_quality={"composite_score": 0.9})
        stray = [p for p in job.root.rglob("*.tmp")]
        assert stray == []
