"""
Tests for the per-page OCR quality scorer.

Covers each signal and each branch of ``decide``:
- non_tibetan_char_ratio
- structural_error_ratio
- sanskrit_adjusted_error_ratio (Sanskrit-flagged errors excluded)
- line_count_sanity
- encoding_error_count hard floor
- Phase-2 unknown_word_ratio captured but currently weighted 0
- decide → accept / escalate / reject branches
"""
import pytest

from app.ocr_assist.quality import (
    OcrDiagnostics,
    PageQuality,
    Thresholds,
    W_PHASE2_UNKNOWN,
    decide,
    score_page,
)


# A pure-Tibetan, mostly-clean page used as a baseline in several tests.
CLEAN_TEXT = "བཀྲ་ཤིས་བདེ་ལེགས།\nདགེ་བའི་བཤེས་གཉེན།"


def err(word: str, error_type: str = "invalid_subscript_combination", severity: str = "error") -> dict:
    return {"word": word, "error_type": error_type, "severity": severity}


class TestSignals:
    def test_clean_page_scores_near_one(self):
        quality = score_page(CLEAN_TEXT, [], OcrDiagnostics())
        assert quality.composite_score > 0.95
        assert quality.structural_error_ratio == 0.0
        assert quality.non_tibetan_char_ratio == 0.0
        assert quality.encoding_error_count == 0

    def test_non_tibetan_chars_lower_score(self):
        garbled = CLEAN_TEXT + " hello world XXXXXX"
        quality = score_page(garbled, [], OcrDiagnostics())
        assert quality.non_tibetan_char_ratio > 0.3
        assert quality.composite_score < score_page(CLEAN_TEXT, [], OcrDiagnostics()).composite_score

    def test_structural_errors_lower_score(self):
        errors = [err("བཀྲ"), err("ཤིས"), err("བདེ")]
        quality = score_page(CLEAN_TEXT, errors, OcrDiagnostics())
        assert quality.structural_error_ratio > 0.0
        assert quality.composite_score < 1.0

    def test_critical_severity_weighs_more_than_error(self):
        crit_q = score_page(CLEAN_TEXT, [err("བཀྲ", severity="critical")], OcrDiagnostics())
        err_q = score_page(CLEAN_TEXT, [err("བཀྲ", severity="error")], OcrDiagnostics())
        assert crit_q.structural_error_ratio > err_q.structural_error_ratio


class TestSanskritAdjustment:
    def test_sanskrit_flagged_errors_excluded_from_adjusted_ratio(self):
        # ཨོཾ contains anusvara (U+0F7E) → Sanskrit detector flags it.
        # ཀྲྀ uses a vocalic-r vowel; included as a non-Sanskrit error for contrast.
        text = "ཨོཾ་མ་ཎི།\nབཀྲ་ཤིས།"
        errors = [
            err("ཨོཾ"),       # should be excluded from sanskrit-adjusted
            err("བཀྲ"),      # pure Tibetan; stays in adjusted
        ]
        quality = score_page(text, errors, OcrDiagnostics())
        # Raw structural ratio reflects both errors; adjusted reflects only one.
        assert quality.sanskrit_adjusted_error_ratio < quality.structural_error_ratio
        assert quality.sanskrit_adjusted_error_ratio > 0.0


class TestLineSanity:
    def test_no_expected_line_count_skips_check(self):
        q = score_page(CLEAN_TEXT, [], OcrDiagnostics(line_count=3, expected_line_count=None))
        assert q.line_count_sanity == 1.0

    def test_line_count_matches_expected_is_perfect(self):
        q = score_page(CLEAN_TEXT, [], OcrDiagnostics(line_count=8, expected_line_count=8))
        assert q.line_count_sanity == 1.0

    def test_line_count_deviates_lowers_sanity(self):
        q = score_page(CLEAN_TEXT, [], OcrDiagnostics(line_count=4, expected_line_count=8))
        assert q.line_count_sanity == pytest.approx(0.5)

    def test_extreme_line_count_floors_at_zero(self):
        q = score_page(CLEAN_TEXT, [], OcrDiagnostics(line_count=0, expected_line_count=2))
        # |0-2|/2 = 1.0 deviation → sanity = 0.0
        assert q.line_count_sanity == 0.0


class TestEncodingErrors:
    def test_encoding_errors_counted(self):
        errors = [
            err("xx", error_type="encoding_error", severity="critical"),
            err("yy", error_type="encoding_error", severity="critical"),
        ]
        q = score_page(CLEAN_TEXT, errors, OcrDiagnostics())
        assert q.encoding_error_count == 2


class TestPhase2Captured:
    def test_unknown_word_ratio_captured_but_weighted_zero(self):
        # Sanity guard on the TODO marker for the corpus-populated future.
        assert W_PHASE2_UNKNOWN == 0.0

        unknown = err("བཀྲ", error_type="unknown_word", severity="warning")
        with_unknown = score_page(CLEAN_TEXT, [unknown], OcrDiagnostics())
        without = score_page(CLEAN_TEXT, [], OcrDiagnostics())

        assert with_unknown.unknown_word_ratio > 0.0
        # Composite must be unaffected while the weight is 0.
        assert with_unknown.composite_score == without.composite_score
        # Unknown words are excluded from the Phase-1 structural ratio.
        assert with_unknown.structural_error_ratio == 0.0


class TestDecide:
    THRESHOLDS = Thresholds(accept=0.85, reject=0.5)

    def _q(self, composite: float, encoding_errors: int = 0) -> PageQuality:
        return PageQuality(
            non_tibetan_char_ratio=0.0,
            structural_error_ratio=0.0,
            sanskrit_adjusted_error_ratio=0.0,
            line_count_sanity=1.0,
            encoding_error_count=encoding_errors,
            unknown_word_ratio=0.0,
            composite_score=composite,
            breakdown={},
        )

    def test_high_score_accepts(self):
        assert decide(self._q(0.95), self.THRESHOLDS) == "accept"

    def test_mid_score_escalates(self):
        assert decide(self._q(0.7), self.THRESHOLDS) == "escalate"

    def test_low_score_rejects(self):
        assert decide(self._q(0.3), self.THRESHOLDS) == "reject"

    def test_encoding_error_blocks_accept(self):
        # Composite would auto-accept, but encoding error forces escalate.
        assert decide(self._q(0.95, encoding_errors=1), self.THRESHOLDS) == "escalate"

    def test_encoding_error_still_rejects_when_score_floor_hit(self):
        # Encoding error + already-below-reject composite → reject, not escalate.
        assert decide(self._q(0.2, encoding_errors=1), self.THRESHOLDS) == "reject"

    def test_boundary_at_accept_threshold(self):
        # composite == accept threshold → accept (>= boundary)
        assert decide(self._q(0.85), self.THRESHOLDS) == "accept"

    def test_boundary_at_reject_threshold(self):
        # composite == reject threshold → escalate (strict <)
        assert decide(self._q(0.5), self.THRESHOLDS) == "escalate"


class TestEmptyText:
    def test_empty_text_has_zero_ratios(self):
        q = score_page("", [], OcrDiagnostics())
        assert q.non_tibetan_char_ratio == 0.0
        assert q.structural_error_ratio == 0.0
        assert q.sanskrit_adjusted_error_ratio == 0.0
        # No expected line count → sanity defaults to 1.0, composite stays 1.0.
        assert q.composite_score == 1.0
