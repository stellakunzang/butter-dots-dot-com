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
- Digital PDFs (fitz extraction) are deterministic, so their genuine-error count
  must match the copy-paste count exactly (tolerance 0).
- OCR-routed fixtures are GOLDEN baselines (see _GOLDEN_OCR). They are clean,
  in-distribution scans of real Tibetan text — the "right circumstances" under
  which OCR should read near-perfectly. Each is pinned to a tight genuine-error
  gap plus per-page Tibetan-character floors, measured once against a trusted
  transcription. These are regression walls: any change that dents a golden read
  fails review. Tighten them when a change improves the read; never loosen them
  to make a regression pass. See docs/planning/OCR_PARITY_BASELINE.md.

  A font whose only OCR relevance is that it *routes* to OCR (e.g. Microsoft
  Himalaya / Tashi Gyedpa) is NOT a golden fixture — its rendered glyphs are
  out-of-distribution and it will never read perfectly. Routing coverage for
  those lives in test_cmap_detection.py; they are excluded here via
  _ROUTING_ONLY_FIXTURES.

Running
-------
  cd backend && pytest tests/test_ocr_parity.py -v

To run only the internal-API tests (faster, no HTTP overhead):
  pytest tests/test_ocr_parity.py::TestPDFPipelineFixtures -v

To run only the full-stack API tests:
  pytest tests/test_ocr_parity.py::TestParityAPIEndpoints -v
"""

import io
from dataclasses import dataclass
from pathlib import Path

import pytest

PARITY_DIR = Path(__file__).parent / "fixtures" / "parity"

# Tolerated absolute difference in genuine error counts for DIGITAL PDFs. fitz
# extraction is deterministic, so a digital PDF must spellcheck identically to
# its copy-paste source. OCR-routed fixtures are governed by _GOLDEN_OCR below,
# not by this constant.
OCR_ERROR_COUNT_TOLERANCE = 0


@dataclass(frozen=True)
class GoldenOCRBaseline:
    """A tight, measured baseline for a clean OCR-routed fixture.

    A golden fixture is a clean, in-distribution scan whose text OCR should read
    near-perfectly. The numbers are measured once against a trusted transcription
    and then act as a regression wall.

    max_gap: the genuine-error gap (|ocr - copy|) must not exceed this. For a
        truly clean page this should be small — ideally 0. A larger value is a
        measured statement about the engine's real ceiling on this page, not a
        tolerance to inflate.
    min_page_tibetan_chars: per-page Tibetan-character floors, one per page, in
        order. A page dropping below its floor (minus a small slack) fails —
        this catches a page collapsing even when the overall gap barely moves.
    allowed_extra_error_types: error types OCR introduces beyond the copy-paste
        set on this page. Keep this as small as the clean read allows; empty is
        the goal. A type outside this recorded set means a NEW category of
        misread — the test fails so the regression is reviewed, not absorbed.
    """

    max_gap: int
    min_page_tibetan_chars: tuple[int, ...]
    allowed_extra_error_types: frozenset[str] = frozenset()


# Golden OCR baselines. Keys are fixture stems. Each is a clean, in-distribution
# scan measured once against a trusted transcription. Do not raise max_gap or
# lower a page floor to make a change pass — that turns the wall into a ramp.
# When a change improves the read, tighten these in the SAME commit.
#
# Both fixtures are single pages of BDRC scan W28732 v15, OCR'd at native
# resolution via extract_scanned's native-image path. Measured against the
# hand-typed transcriptions in the same directory.
_GOLDEN_OCR: dict[str, GoldenOCRBaseline] = {
    # Page 8: dense, in-distribution body text — the "right circumstances" page.
    # OCR reads it with zero extra genuine errors. The one artefact is the hung
    # seed syllable ཧཱུྂ: when OCR drops its candrabindu the glyph becomes ཧཱུ,
    # which is no longer a Sanskrit marker, so it surfaces as a double_vowel
    # rather than an info-level Sanskrit note.
    "tibetan-baseline-W28732": GoldenOCRBaseline(
        max_gap=0,
        min_page_tibetan_chars=(820,),
        allowed_extra_error_types=frozenset({"double_vowel"}),
    ),
    # Page 1 of the Menla (Medicine Buddha) sadhana: Sanskrit-heavy (mantras +
    # seed syllables). A harder read than the body page — OCR introduces a few
    # genuine misreads: an injected Latin glyph and a stray '+' prefix (both
    # unparsed_characters) and a consonant-after-vowel. With the common Sanskrit
    # forms now allowlisted (padma etc.), these OCR-only garbage reads are what
    # remains of the gap. The line-1 seed syllable ཧཱུྃ is misread either way:
    # ཧ-H under the frame rule, ཧར-MH once whiten_rule_above paints the rule
    # out (issue #79). Same edit distance, but the clean-crop read surfaces as
    # invalid_post_suffix.
    "menla-sadhana-sanskrit-W28732": GoldenOCRBaseline(
        max_gap=2,
        min_page_tibetan_chars=(753,),
        allowed_extra_error_types=frozenset(
            {"consonant_after_vowel", "unparsed_characters", "invalid_post_suffix"}
        ),
    ),
    # Continuity Camera still of one pecha leaf (Photo Booth, 1470x980): six
    # lines of uchen prose under a thin frame rule (issue #79). Guards the
    # first-line bound (line 1 was garbage without it) on a photo, not a scan.
    # Transcription hand-corrected against the leaf. Measured with the
    # dictionary off, as in CI; one OCR misread surfaces as invalid_post_suffix.
    "pecha-photo-leaf1-prose": GoldenOCRBaseline(
        max_gap=1,
        min_page_tibetan_chars=(823,),
        allowed_extra_error_types=frozenset({"invalid_post_suffix"}),
    ),
    # Same pecha, next leaf: a section opening (yig mgo, an outline of
    # སྒྲུབ / སྒྲོལ stacks, ༔ marks), then prose. A hard page, pinned at today's
    # read rather than a clean one: the yig mgo and several stacks still
    # misread. Guards the vertical line margin, which only fires here.
    # Dictionary off, as in CI.
    "pecha-photo-leaf2-section-opening": GoldenOCRBaseline(
        max_gap=3,
        min_page_tibetan_chars=(436,),
        allowed_extra_error_types=frozenset(
            {"invalid_subscript_combination", "invalid_suffix", "multiple_vowels"}
        ),
    ),
}

# A page's Tibetan-character count may sit at most this many characters below
# its recorded floor before a golden fixture fails. Kept small on purpose.
_PAGE_CHAR_DROP_SLACK = 10

# Fixtures that route to OCR only because of a broken font encoding (ADR-015),
# not because they are representative OCR targets. Their rendered glyphs are
# out-of-distribution, so they are never golden. Routing coverage lives in
# test_cmap_detection.py; they are skipped by the parity oracle here.
_ROUTING_ONLY_FIXTURES = {"Tashi Gyedpa"}

# Fixtures that require the BDRC OCR engine + downloaded ONNX models.
# Skipped in CI when Models/ is absent (tps is optional since #59).
_OCR_REQUIRED_FIXTURES = set(_GOLDEN_OCR)

_LINE_MODEL = Path(__file__).resolve().parents[1] / "Models" / "Lines" / "PhotiLines.onnx"


def _ocr_available() -> bool:
    try:
        import pyctcdecode  # noqa: F401
    except ImportError:
        return False
    return _LINE_MODEL.is_file()


OCR_AVAILABLE = _ocr_available()

# Module-level cache so PDF extraction runs exactly once per PDF per test session.
_pdf_cache: dict[Path, list] = {}

# Informational notes the engine emits that are NOT genuine spelling errors:
# OCR noise skipped as non-Tibetan, and Sanskrit transliteration flagged by the
# engine (mantras/dharanis written in Tibetan script). They carry severity
# "info" and appear on both the copy-paste and OCR sides, so they are excluded
# from the error-type comparison. Genuine-error COUNTING uses severity directly
# (see _genuine_error_count) so any new info type is handled automatically.
INFO_ONLY_TYPES = {
    "non_tibetan_skipped",
    "foreign_transliteration",
    "sanskrit_marker",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _error_types(errors: list[dict]) -> set[str]:
    return {e.get("error_type", "") for e in errors}


def _genuine_error_count(errors: list[dict]) -> int:
    """Count of genuine spelling errors — excludes info-level notes.

    Info notes (non-Tibetan skipped, Sanskrit transliteration) are not spelling
    errors, so they must not inflate the copy-paste vs OCR gap. Using severity
    rather than an explicit type list means a new info category is excluded
    automatically.
    """
    return sum(1 for e in errors if e.get("severity") != "info")


def _tibetan_char_count(text: str) -> int:
    """Count of characters in the Tibetan Unicode block (U+0F00–U+0FFF)."""
    return sum(1 for c in text if 0x0F00 <= ord(c) <= 0x0FFF)


def _gap_ceiling(stem: str) -> int:
    """Max genuine-error gap: the golden baseline's for OCR fixtures, else 0."""
    golden = _GOLDEN_OCR.get(stem)
    return golden.max_gap if golden else OCR_ERROR_COUNT_TOLERANCE


def _allowed_extra_types(stem: str) -> frozenset[str]:
    """Error types an OCR fixture may introduce beyond copy-paste; empty for digital."""
    golden = _GOLDEN_OCR.get(stem)
    return golden.allowed_extra_error_types if golden else frozenset()


def _pdf_pages(pdf_path: Path) -> list:
    """
    Extract pages from a PDF using the real pipeline routing logic (extract_pdf).

    For digital PDFs this uses fitz; for scanned PDFs (or digital PDFs with a
    broken CMap) it falls back to OCR. Results are cached so extraction runs
    exactly once per PDF per test session.

    Calls pytest.skip() if the OCR engine is unavailable, so CI stays green
    when the optional pyctcdecode dependency is not installed.
    """
    if pdf_path not in _pdf_cache:
        from app.pdf.extractor import extract_pdf

        try:
            pages, _ = extract_pdf(pdf_path.read_bytes())
        except RuntimeError as e:
            if "OCR engine unavailable" in str(e):
                pytest.skip(f"OCR engine not available — install pyctcdecode to run: {e}")
            raise
        _pdf_cache[pdf_path] = pages
    return _pdf_cache[pdf_path]


def _load_fixture_cases() -> list[pytest.param]:
    """Discover (txt, pdf) fixture pairs under parity/, minus routing-only ones.

    Routing-only fixtures (e.g. Tashi Gyedpa) keep their .pdf in the directory
    for test_cmap_detection.py, but are not fidelity cases here.
    """
    cases = []
    if PARITY_DIR.exists():
        for txt_path in sorted(PARITY_DIR.glob("*.txt")):
            if txt_path.stem in _ROUTING_ONLY_FIXTURES:
                continue
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

        allowed_extra = _allowed_extra_types(txt_path.stem)
        pdf_only_types = pdf_types - copy_types - INFO_ONLY_TYPES - allowed_extra
        assert not pdf_only_types, (
            f"[{txt_path.stem}] PDF pipeline introduced unexpected error types:\n"
            f"  PDF-only (new): {sorted(pdf_only_types)}\n"
            f"  Copy-paste:     {sorted(copy_types)}\n"
            f"  PDF total:      {sorted(pdf_types)}\n"
            "For a digital PDF this signals an extraction regression. For a golden "
            "OCR fixture it means a NEW misread category appeared beyond the recorded "
            "baseline — review it, then add to the golden allowed_extra_error_types "
            "only if it is a genuine, acceptable OCR artefact."
        )

    @pytest.mark.parametrize("txt_path,pdf_path", _FIXTURE_CASES)
    def test_genuine_error_gap_within_golden_ceiling(self, txt_path, pdf_path, spellchecker):
        """
        The genuine-error gap between copy-paste and PDF-pipeline output must not
        exceed the fixture's ceiling: 0 for digital PDFs, or the golden baseline's
        max_gap for OCR-routed fixtures. A growing gap means the read got worse.
        """
        stem = txt_path.stem
        ceiling = _gap_ceiling(stem)

        ground_truth = txt_path.read_text(encoding="utf-8").strip()
        copy_count = _genuine_error_count(spellchecker.check_text(ground_truth))

        pages = _pdf_pages(pdf_path)
        pdf_text = "\n".join(p.text for p in pages)
        pdf_count = _genuine_error_count(spellchecker.check_text(pdf_text))

        gap = abs(pdf_count - copy_count)
        if stem in _GOLDEN_OCR:
            assert gap <= ceiling, (
                f"[{stem}] golden OCR gap grew to {gap} "
                f"(copy-paste: {copy_count}, OCR: {pdf_count}); golden ceiling is "
                f"{ceiling}. A larger gap means OCR read this clean page worse. Do NOT "
                "raise the ceiling to make this pass — see "
                "docs/planning/OCR_PARITY_BASELINE.md."
            )
        else:
            assert gap <= ceiling, (
                f"[{stem}] Genuine error count differs by {gap} "
                f"(copy-paste: {copy_count}, PDF: {pdf_count}, tolerance: {ceiling}). "
                "For a digital PDF this should be zero — check for a fitz extraction "
                "regression."
            )

    @pytest.mark.parametrize("txt_path,pdf_path", _FIXTURE_CASES)
    def test_pdf_produces_tibetan_content(self, txt_path, pdf_path):
        """
        Sanity check: the PDF pipeline should extract a non-trivial amount of
        Tibetan text. For golden OCR fixtures, also enforce the per-page
        character floor — a collapsing page is a regression even if the gap
        barely moves.
        """
        stem = txt_path.stem
        pages = _pdf_pages(pdf_path)
        all_text = "\n".join(p.text for p in pages)

        total_tibetan = _tibetan_char_count(all_text)
        assert total_tibetan >= 50, (
            f"[{stem}] PDF pipeline returned too few Tibetan characters "
            f"({total_tibetan} < 50). "
            "Check that fitz or the OCR engine is working correctly for this PDF."
        )

        golden = _GOLDEN_OCR.get(stem)
        if golden is None:
            return

        floors = golden.min_page_tibetan_chars
        assert len(pages) == len(floors), (
            f"[{stem}] OCR returned {len(pages)} pages but the golden baseline records "
            f"{len(floors)}. Re-measure and update min_page_tibetan_chars."
        )
        for page, floor in zip(pages, floors):
            chars = _tibetan_char_count(page.text)
            assert chars >= floor - _PAGE_CHAR_DROP_SLACK, (
                f"[{stem}] page {page.page_number} Tibetan-character count dropped to "
                f"{chars}; golden floor is {floor} (slack {_PAGE_CHAR_DROP_SLACK}). A "
                "page collapsing like this is a read regression. See "
                "docs/planning/OCR_PARITY_BASELINE.md — do NOT lower the floor to pass."
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
        if txt_path.stem in _OCR_REQUIRED_FIXTURES and not OCR_AVAILABLE:
            pytest.skip("OCR models/deps unavailable — skipping OCR-required fixture")
        ground_truth = txt_path.read_text(encoding="utf-8").strip()

        text_resp = client.post("/api/v1/spellcheck/text", json={"text": ground_truth})
        assert (
            text_resp.status_code == 200
        ), f"Text endpoint returned {text_resp.status_code}: {text_resp.text}"
        copy_types = _error_types(text_resp.json()["errors"])

        pdf_bytes = pdf_path.read_bytes()
        upload_resp = client.post(
            "/api/v1/spellcheck/upload",
            files={"file": (pdf_path.name, io.BytesIO(pdf_bytes), "application/pdf")},
        )
        assert (
            upload_resp.status_code == 200
        ), f"Upload endpoint returned {upload_resp.status_code}: {upload_resp.text}"
        assert "errors" in upload_resp.json(), (
            "Upload response is missing 'errors' key — got an async response instead of sync. "
            "Check that the fixture PDF is within the sync page limit."
        )
        ocr_types = _error_types(upload_resp.json()["errors"])

        allowed_extra = _allowed_extra_types(txt_path.stem)
        ocr_only_types = ocr_types - copy_types - INFO_ONLY_TYPES - allowed_extra
        assert not ocr_only_types, (
            f"[{txt_path.stem}] API: OCR introduced unexpected error types:\n"
            f"  OCR-only (new): {sorted(ocr_only_types)}\n"
            f"  Copy-paste:     {sorted(copy_types)}\n"
            f"  OCR total:      {sorted(ocr_types)}\n"
            "A type here is a NEW misread category beyond the golden baseline — "
            "review before adding to allowed_extra_error_types."
        )

    @pytest.mark.parametrize("txt_path,pdf_path", _FIXTURE_CASES)
    def test_api_error_count_parity(self, txt_path, pdf_path, client):
        """Error counts via the API should be within the fixture's gap ceiling."""
        if txt_path.stem in _OCR_REQUIRED_FIXTURES and not OCR_AVAILABLE:
            pytest.skip("OCR models/deps unavailable — skipping OCR-required fixture")
        tolerance = _gap_ceiling(txt_path.stem)

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
        assert diff <= tolerance, (
            f"[{txt_path.stem}] API: error count differs by {diff} "
            f"(copy-paste: {copy_count}, PDF: {ocr_count}, ceiling: {tolerance}).\n"
            "For a digital PDF this should be zero — check for a fitz extraction "
            "regression. For an OCR-routed fixture a larger gap means the read "
            "regressed; see docs/planning/OCR_PARITY_BASELINE.md."
        )
