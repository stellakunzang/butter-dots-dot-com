"""
PDF pipeline vs copy-paste spellcheck parity tests.

For each fixture pair in tests/fixtures/parity/, compare the spellcheck output
from the copy-paste path (text string direct to the engine) against the PDF
pipeline path (same content presented as a PDF — digital or scanned).

Fixture format
--------------
Each test case is a pair of files with matching stems:
  backend/tests/fixtures/parity/<name>.txt   ← ground-truth (copy-paste) text
  backend/tests/fixtures/parity/<name>.pdf   ← PDF of the same text (digital or scanned)

Discovery is automatic — any .txt with a same-stem .pdf in the parity/ directory
becomes a parametrized test case.

Comparison criteria
-------------------
- Error types that appear in PDF pipeline output but are absent in the copy-paste result
  (excluding "non_tibetan_skipped", which is tolerated) cause a failure.
- The count of genuine spelling errors is compared within a tolerance of ±2 by
  default. Increase OCR_ERROR_COUNT_TOLERANCE for texts where OCR drift is
  expected (e.g. lower-resolution scans).

Running
-------
  cd backend && pytest tests/test_ocr_parity.py -v

To run only the internal-API tests (faster, no HTTP overhead):
  pytest tests/test_ocr_parity.py::TestPDFPipelineFixtures -v

To run only the full-stack API tests:
  pytest tests/test_ocr_parity.py::TestParityAPIEndpoints -v
"""
import io
from pathlib import Path

import pytest

PARITY_DIR = Path(__file__).parent / "fixtures" / "parity"

# Tolerated absolute difference in genuine error counts between copy-paste and
# OCR paths. Currently 0 because all fixtures are clean digital PDFs (fitz
# extraction is deterministic). When adding a scanned fixture, move this to a
# per-fixture dict rather than raising the global.
OCR_ERROR_COUNT_TOLERANCE = 0

# Module-level cache so PDF extraction runs exactly once per PDF per test session.
_pdf_cache: dict[Path, list] = {}

# Error types that are acceptable in PDF pipeline output even if absent in copy-paste
# (OCR may misread individual glyphs as non-Tibetan characters).
TOLERATED_OCR_ONLY_TYPES = {"non_tibetan_skipped"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _error_types(errors: list[dict]) -> set[str]:
    return {e.get("error_type", "") for e in errors}


def _genuine_error_count(errors: list[dict]) -> int:
    """Count of errors that are not informational OCR-noise messages."""
    return sum(1 for e in errors if e.get("error_type") not in TOLERATED_OCR_ONLY_TYPES)


def _pdf_pages(pdf_path: Path) -> list:
    """
    Extract pages from a PDF using the real pipeline routing logic (extract_pdf).

    For digital PDFs this uses fitz; for scanned PDFs (or digital PDFs with a
    broken CMap) it falls back to OCR. Results are cached so extraction runs
    exactly once per PDF per test session.
    """
    if pdf_path not in _pdf_cache:
        from app.pdf.extractor import extract_pdf
        pages, _ = extract_pdf(pdf_path.read_bytes())
        _pdf_cache[pdf_path] = pages
    return _pdf_cache[pdf_path]


def _load_fixture_cases() -> list[pytest.param]:
    """Discover all (txt, pdf) fixture pairs under the parity/ directory."""
    cases = []
    if PARITY_DIR.exists():
        for txt_path in sorted(PARITY_DIR.glob("*.txt")):
            pdf_path = txt_path.with_suffix(".pdf")
            if pdf_path.exists():
                cases.append(pytest.param(txt_path, pdf_path, id=txt_path.stem))
    return cases


# ---------------------------------------------------------------------------
# Sentinel: skip cleanly when no fixtures exist yet
# ---------------------------------------------------------------------------

class TestNoFixturesYet:
    """Keeps the suite green while the parity/ directory is still empty."""

    def test_fixtures_directory_exists(self):
        assert PARITY_DIR.exists(), (
            f"Parity fixtures directory not found: {PARITY_DIR}\n"
            "Run: mkdir -p backend/tests/fixtures/parity\n"
            "See .cursor/skills/spellcheck-ocr-parity/SKILL.md for instructions."
        )

    def test_at_least_one_fixture_exists(self):
        """At least one .txt/.pdf fixture pair must be present in the parity/ directory."""
        cases = _load_fixture_cases()
        assert cases, (
            "No parity fixtures found. "
            "Add .txt + .pdf pairs to backend/tests/fixtures/parity/ to enable "
            "parity testing. See .cursor/skills/spellcheck-ocr-parity/SKILL.md."
        )


# ---------------------------------------------------------------------------
# Internal-API parity: engine called directly
# ---------------------------------------------------------------------------

_FIXTURE_CASES = _load_fixture_cases()


@pytest.mark.slow
@pytest.mark.skipif(not _FIXTURE_CASES, reason="No parity fixtures found")
class TestPDFPipelineFixtures:
    """
    Compare TibetanSpellChecker output for copy-paste text vs PDF-pipeline-extracted
    text from the paired PDF fixture (digital or scanned).

    Uses extract_pdf() — the real routing function — so digital PDFs go through
    fitz and scanned PDFs go through OCR, matching actual user-facing behaviour.
    """

    @pytest.fixture(scope="class")
    def spellchecker(self):
        from app.spellcheck.engine import TibetanSpellChecker
        return TibetanSpellChecker()

    @pytest.mark.parametrize("txt_path,pdf_path", _FIXTURE_CASES)
    def test_no_unexpected_pdf_error_types(self, txt_path, pdf_path, spellchecker):
        """
        Error types introduced by the PDF pipeline (beyond tolerated noise types)
        should not appear in PDF output if they are absent in the copy-paste result.
        """
        ground_truth = txt_path.read_text(encoding="utf-8").strip()
        copy_errors = spellchecker.check_text(ground_truth)
        copy_types = _error_types(copy_errors)

        pages = _pdf_pages(pdf_path)
        pdf_text = "\n".join(p.text for p in pages)
        pdf_errors = spellchecker.check_text(pdf_text)
        pdf_types = _error_types(pdf_errors)

        pdf_only_types = pdf_types - copy_types - TOLERATED_OCR_ONLY_TYPES
        assert not pdf_only_types, (
            f"[{txt_path.stem}] PDF pipeline introduced unexpected error types:\n"
            f"  PDF-only:    {sorted(pdf_only_types)}\n"
            f"  Copy-paste:  {sorted(copy_types)}\n"
            f"  PDF total:   {sorted(pdf_types)}\n"
            "This may indicate a text extraction regression or a new error type "
            "that should be added to TOLERATED_OCR_ONLY_TYPES if expected."
        )

    @pytest.mark.parametrize("txt_path,pdf_path", _FIXTURE_CASES)
    def test_genuine_error_count_within_tolerance(self, txt_path, pdf_path, spellchecker):
        """
        The number of genuine (non-noise) spellcheck errors should be within
        OCR_ERROR_COUNT_TOLERANCE of the copy-paste count.
        """
        ground_truth = txt_path.read_text(encoding="utf-8").strip()
        copy_errors = spellchecker.check_text(ground_truth)
        copy_count = _genuine_error_count(copy_errors)

        pages = _pdf_pages(pdf_path)
        pdf_text = "\n".join(p.text for p in pages)
        pdf_errors = spellchecker.check_text(pdf_text)
        pdf_count = _genuine_error_count(pdf_errors)

        diff = abs(pdf_count - copy_count)
        assert diff <= OCR_ERROR_COUNT_TOLERANCE, (
            f"[{txt_path.stem}] Genuine error count differs by {diff} "
            f"(copy-paste: {copy_count}, PDF: {pdf_count}).\n"
            "For a digital PDF this should be zero — check for a fitz extraction "
            "regression. For a scanned fixture, introduce a per-fixture tolerance "
            "dict rather than raising OCR_ERROR_COUNT_TOLERANCE globally."
        )

    @pytest.mark.parametrize("txt_path,pdf_path", _FIXTURE_CASES)
    def test_pdf_produces_tibetan_content(self, txt_path, pdf_path):
        """
        Sanity check: the PDF pipeline should extract a non-trivial amount of
        Tibetan text. Guards against silent extraction failures.
        """
        pages = _pdf_pages(pdf_path)
        all_text = "\n".join(p.text for p in pages)

        tibetan_chars = [c for c in all_text if 0x0F00 <= ord(c) <= 0x0FFF]
        assert len(tibetan_chars) >= 50, (
            f"[{txt_path.stem}] PDF pipeline returned too few Tibetan characters "
            f"({len(tibetan_chars)} < 50). "
            "Check that fitz or the OCR engine is working correctly for this PDF."
        )


# ---------------------------------------------------------------------------
# Full-stack API parity: exercises the HTTP layer
# ---------------------------------------------------------------------------

@pytest.mark.slow
@pytest.mark.skipif(not _FIXTURE_CASES, reason="No parity fixtures found")
class TestParityAPIEndpoints:
    """
    Same parity check but through the FastAPI HTTP layer using TestClient.
    Slower than TestOCRParityFixtures but exercises request validation,
    response serialisation, and the full PDF processing pipeline.

    Note: these tests assume /spellcheck/upload always returns a synchronous
    PDFUploadSyncResponse with an "errors" key. That holds because the async
    routing is currently disabled (all PDFs go through _process_sync). If the
    page-count threshold is re-enabled, large fixture PDFs would return a
    PDFUploadAsyncResponse (no "errors" key) and these tests would need updating.
    """

    @pytest.fixture(scope="class")
    def client(self):
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    @pytest.mark.parametrize("txt_path,pdf_path", _FIXTURE_CASES)
    def test_api_error_types_parity(self, txt_path, pdf_path, client):
        """
        POST to /spellcheck/text and /spellcheck/upload should produce
        consistent error type sets for the same underlying text.
        """
        ground_truth = txt_path.read_text(encoding="utf-8").strip()

        text_resp = client.post("/api/v1/spellcheck/text", json={"text": ground_truth})
        assert text_resp.status_code == 200, (
            f"Text endpoint returned {text_resp.status_code}: {text_resp.text}"
        )
        copy_types = _error_types(text_resp.json()["errors"])

        pdf_bytes = pdf_path.read_bytes()
        upload_resp = client.post(
            "/api/v1/spellcheck/upload",
            files={"file": (pdf_path.name, io.BytesIO(pdf_bytes), "application/pdf")},
        )
        assert upload_resp.status_code == 200, (
            f"Upload endpoint returned {upload_resp.status_code}: {upload_resp.text}"
        )
        assert "errors" in upload_resp.json(), (
            "Upload response is missing 'errors' key — got an async response instead of sync. "
            "Check that the fixture PDF is within the sync page limit."
        )
        ocr_types = _error_types(upload_resp.json()["errors"])

        ocr_only_types = ocr_types - copy_types - TOLERATED_OCR_ONLY_TYPES
        assert not ocr_only_types, (
            f"[{txt_path.stem}] API: OCR introduced unexpected error types:\n"
            f"  OCR-only:   {sorted(ocr_only_types)}\n"
            f"  Copy-paste: {sorted(copy_types)}\n"
            f"  OCR total:  {sorted(ocr_types)}"
        )

    @pytest.mark.parametrize("txt_path,pdf_path", _FIXTURE_CASES)
    def test_api_error_count_parity(self, txt_path, pdf_path, client):
        """Error counts via the API should be within OCR_ERROR_COUNT_TOLERANCE."""
        ground_truth = txt_path.read_text(encoding="utf-8").strip()

        text_resp = client.post("/api/v1/spellcheck/text", json={"text": ground_truth})
        assert text_resp.status_code == 200
        copy_count = _genuine_error_count(text_resp.json()["errors"])

        pdf_bytes = pdf_path.read_bytes()
        upload_resp = client.post(
            "/api/v1/spellcheck/upload",
            files={"file": (pdf_path.name, io.BytesIO(pdf_bytes), "application/pdf")},
        )
        assert upload_resp.status_code == 200
        assert "errors" in upload_resp.json(), (
            "Upload response is missing 'errors' key — got an async response instead of sync. "
            "Check that the fixture PDF is within the sync page limit."
        )
        ocr_count = _genuine_error_count(upload_resp.json()["errors"])

        diff = abs(ocr_count - copy_count)
        assert diff <= OCR_ERROR_COUNT_TOLERANCE, (
            f"[{txt_path.stem}] API: error count differs by {diff} "
            f"(copy-paste: {copy_count}, PDF: {ocr_count}).\n"
            "For a digital PDF this should be zero — check for a fitz extraction "
            "regression. For a scanned fixture, introduce a per-fixture tolerance "
            "dict rather than raising OCR_ERROR_COUNT_TOLERANCE globally."
        )
