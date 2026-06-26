"""
Calibration regression tests for T-10/T-11/T-13 on scanned-pecha fixtures.

Uses human-labeled pages from the calibration fixtures documented in
``docs/planning/INTERACTIVE_OCR_PLAN.md`` § Quality scorer calibration.
(job ``4bed0eb14c9f``, ``pages_for_ocr_test.pdf``). Word bilingual PDFs are
out of scope — these fixtures are scanned pecha only.
"""
from pathlib import Path

import pytest

from app.ocr_assist.quality import (
    OcrDiagnostics,
    ScoringContext,
    Thresholds,
    decide,
    score_page,
)
from app.ocr_assist.runner import DEFAULT_THRESHOLDS
from app.spellcheck.engine import TibetanSpellChecker


FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "ocr_smoke"
THRESHOLDS = DEFAULT_THRESHOLDS
PECHA_CONTEXT = ScoringContext(expect_mixed_script=False)


@pytest.fixture(scope="module")
def checker() -> TibetanSpellChecker:
    return TibetanSpellChecker()


def _load_page_ocr(page: int) -> str:
    path = FIXTURE_ROOT / f"page-{page:03d}.txt"
    if not path.is_file():
        pytest.skip(f"fixture missing: {path}")
    return path.read_text()


def _score_fixture(
    checker: TibetanSpellChecker,
    page: int,
    *,
    line_count: int,
    expected_line_count: int | None = None,
    ocr_text: str | None = None,
):
    text = ocr_text if ocr_text is not None else _load_page_ocr(page)
    errors = checker.check_text(text)
    diagnostics = OcrDiagnostics(
        line_count=line_count,
        expected_line_count=expected_line_count,
    )
    quality = score_page(
        text,
        errors,
        diagnostics,
    )
    verdict = decide(
        quality, THRESHOLDS, context=PECHA_CONTEXT, ocr_diagnostics=diagnostics
    )
    return quality, verdict


class TestSmokeFalseAcceptFixtures:
    """Pages a human labeled should-not-auto-accept (primary fixtures)."""

    def test_page_19_dropped_line_escalates_with_baseline(self, checker):
        # Sequential job baseline after early pages ≈26 lines; page 19 → 8 lines.
        quality, verdict = _score_fixture(
            checker, 19, line_count=8, expected_line_count=26
        )
        assert quality.line_count_sanity < 0.35
        assert verdict != "accept"

    def test_page_17_acha_repetition_escalates(self, checker):
        quality, verdict = _score_fixture(checker, 17, line_count=15)
        assert quality.repetition_run_length >= 8
        assert verdict != "accept"

    def test_page_14_latin_contamination_escalates(self, checker):
        # Smoke doc: stray Latin S. Current job artifact may lack S — inject it.
        text = _load_page_ocr(14)
        contaminated = text.replace("པ་ར་བྱུ་ར་ཅིབ", "པ་ར་བྱུ་ར་ཅིS", 1)
        quality, verdict = _score_fixture(
            checker,
            14,
            line_count=25,
            expected_line_count=14,
            ocr_text=contaminated,
        )
        assert quality.latin_letter_count >= 1
        assert verdict != "accept"

    def test_page_20_short_page_escalates_with_baseline(self, checker):
        quality, verdict = _score_fixture(
            checker, 20, line_count=1, expected_line_count=14
        )
        assert quality.line_count_sanity < 0.2
        assert verdict != "accept"

    def test_page_20_minimal_content_escalates_despite_high_composite(self, checker):
        # TIF-style partial page: ~2 syllables, composite can still read 1.0.
        quality, verdict = _score_fixture(
            checker,
            20,
            line_count=1,
            ocr_text="འོད་གསལ",
        )
        assert quality.tibetan_syllable_count < 3
        assert quality.composite_score >= 0.9
        assert verdict != "accept"


class TestStrayLatinRegression:
    @pytest.mark.parametrize("page", [2, 6, 15])
    def test_stray_latin_letter_escalates(self, checker, page: int):
        _, verdict = _score_fixture(checker, page, line_count=25, expected_line_count=14)
        assert verdict != "accept"


class TestMinimumContentFloor:
    def test_two_syllable_page_escalates(self, checker):
        text = "བཀྲ་ཤིས"
        errors = checker.check_text(text)
        quality = score_page(text, errors, OcrDiagnostics(line_count=1))
        assert quality.tibetan_syllable_count < 3
        assert decide(quality, THRESHOLDS, context=PECHA_CONTEXT) != "accept"


class TestGoodPagesStillAccept:
    @pytest.mark.parametrize("page", [1, 4, 12])
    def test_representative_clean_pages_accept(self, checker, page: int):
        quality, verdict = _score_fixture(checker, page, line_count=14)
        assert quality.latin_letter_count == 0
        assert quality.repetition_run_length < 8 or quality.repetition_char != "\u0f68"
        assert quality.composite_score >= THRESHOLDS.accept
        assert verdict == "accept"


class TestMixedScriptLayer1:
    def test_bilingual_page_accepts_on_tibetan_only_score(self, checker):
        text = "བཀྲ་ཤིས་བདེ་ལེགས།\nThis is an English translation paragraph.\n"
        errors = checker.check_text(text)
        quality = score_page(text, errors, OcrDiagnostics(line_count=2))
        assert quality.non_tibetan_char_ratio >= 0.15
        assert quality.tibetan_only_composite_score >= THRESHOLDS.accept
        verdict = decide(
            quality,
            THRESHOLDS,
            context=ScoringContext(expect_mixed_script=True),
        )
        assert verdict == "accept"

    def test_scattered_latin_on_pecha_still_escalates(self, checker):
        text = _load_page_ocr(2)
        errors = checker.check_text(text)
        quality = score_page(text, errors, OcrDiagnostics(line_count=25))
        verdict = decide(quality, THRESHOLDS, context=PECHA_CONTEXT)
        assert quality.latin_letter_count >= 1
        assert verdict != "accept"
