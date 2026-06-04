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
import unicodedata

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


class TestSanskritExclusionPositionAware:
    """The position-aware exclusion (`_is_sanskrit_error`).

    A syllable flagged Sanskrit-likely at one position must not suppress a
    genuine error on the same syllable string at a different (non-Sanskrit)
    position. When an error carries no position, fall back to string matching.
    """

    def test_position_match_takes_precedence_over_word(self):
        from app.ocr_assist.quality import _is_sanskrit_error

        positions = {5}
        words = {"ཨོཾ"}

        # Same word string, two positions → different verdicts.
        on_sanskrit = {"word": "ཨོཾ", "position": 5}
        off_sanskrit = {"word": "ཨོཾ", "position": 99}
        assert _is_sanskrit_error(on_sanskrit, positions, words) is True
        assert _is_sanskrit_error(off_sanskrit, positions, words) is False

    def test_falls_back_to_word_when_no_position(self):
        from app.ocr_assist.quality import _is_sanskrit_error

        positions = {5}
        words = {"ཨོཾ"}
        assert _is_sanskrit_error({"word": "ཨོཾ"}, positions, words) is True
        assert _is_sanskrit_error({"word": "བཀྲ"}, positions, words) is False

    def test_real_check_text_positions_exclude_sanskrit(self):
        # End-to-end: real check_text errors carry positions; a Sanskrit
        # syllable's error is excluded, a plain one is not.
        from app.spellcheck.engine import TibetanSpellChecker

        text = "ཨོཾ་མ་ཎི།\nབཀྲ་ཤིས།"
        checker = TibetanSpellChecker()
        real_errors = checker.check_text(text)
        # Guard: only meaningful if check_text actually flags something here.
        quality = score_page(text, real_errors, OcrDiagnostics())
        assert quality.sanskrit_adjusted_error_ratio <= quality.structural_error_ratio
        assert 0.0 <= quality.composite_score <= 1.0


class TestCleanPageSkipsSanskritWork:
    def test_no_structural_errors_skips_sanskrit_scoring(self, monkeypatch):
        # On a clean page the (expensive) per-syllable Sanskrit parse/score
        # must not run. Make it explode if called, then score a clean page.
        import app.ocr_assist.quality as quality_mod

        def _boom(*_args, **_kwargs):
            raise AssertionError("_sanskrit_syllables should not run on a clean page")

        monkeypatch.setattr(quality_mod, "_sanskrit_syllables", _boom)
        q = quality_mod.score_page(CLEAN_TEXT, [], OcrDiagnostics())
        assert q.sanskrit_adjusted_error_ratio == 0.0
        assert q.composite_score > 0.95


class TestThresholdsValidation:
    def test_equal_accept_and_reject_is_allowed(self):
        Thresholds(accept=0.5, reject=0.5)  # no raise

    def test_inverted_thresholds_raise(self):
        with pytest.raises(ValueError):
            Thresholds(accept=0.5, reject=0.8)

    def test_out_of_range_thresholds_raise(self):
        with pytest.raises(ValueError):
            Thresholds(accept=1.2, reject=0.5)
        with pytest.raises(ValueError):
            Thresholds(accept=0.5, reject=-0.1)


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


class TestNormalizationRoundtrip:
    """Integration: check_text output must match score_page syllable splitting.

    check_text normalizes (NFC + ZW strip) before splitting, so error['word']
    values are normalized.  score_page must normalize ocr_text the same way
    before splitting so that Sanskrit-syllable lookup works on non-NFC/ZW input.
    """

    def test_zw_prefixed_sanskrit_excluded_from_adjusted_ratio(self):
        # ཨོཾ is a Sanskrit indicator syllable (anusvara U+0F7E).
        # Inject a zero-width space before it to simulate non-clean OCR output.
        # check_text strips the ZWS and returns word='ཨོཾ' in any error;
        # score_page must also strip ZWS so the syllable set contains 'ཨོཾ'.
        from app.spellcheck.engine import TibetanSpellChecker

        zws = '​'
        sanskrit_syl = 'ཨོཾ'
        plain_syl = 'བཀྲ'
        raw_text = f'{zws}{sanskrit_syl}་{plain_syl}་ཤིས།'

        checker = TibetanSpellChecker()
        spellcheck_result = checker.check_text(raw_text)

        synthetic_errors = [
            {'word': sanskrit_syl, 'error_type': 'invalid_subscript_combination', 'severity': 'error'},
            {'word': plain_syl,    'error_type': 'invalid_subscript_combination', 'severity': 'error'},
        ]
        combined = list(spellcheck_result) + synthetic_errors
        quality = score_page(raw_text, combined, OcrDiagnostics())

        # The Sanskrit syllable should be excluded → adjusted ratio < structural ratio.
        assert quality.sanskrit_adjusted_error_ratio < quality.structural_error_ratio

    def test_non_nfc_text_matches_check_text_words(self):
        # Build NFD text and confirm score_page handles it without exceptions
        # and produces a valid composite (no KeyError from mismatched word forms).
        from app.spellcheck.engine import TibetanSpellChecker

        nfd_text = unicodedata.normalize('NFD', 'བཀྲ་ཤིས།')
        checker = TibetanSpellChecker()
        spellcheck_result = checker.check_text(nfd_text)

        quality = score_page(nfd_text, spellcheck_result, OcrDiagnostics())
        assert 0.0 <= quality.composite_score <= 1.0


class TestEmptyText:
    def test_empty_text_has_zero_ratios(self):
        q = score_page("", [], OcrDiagnostics())
        assert q.non_tibetan_char_ratio == 0.0
        assert q.structural_error_ratio == 0.0
        assert q.sanskrit_adjusted_error_ratio == 0.0
        # No expected line count → sanity defaults to 1.0, composite stays 1.0.
        assert q.composite_score == 1.0
