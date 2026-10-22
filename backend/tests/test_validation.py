"""
Tests for Tibetan Syllable Validation

Tests the validation stage (validation/):
- Pattern checks (encoding errors, unusual marks)
- Structural completeness checks
- Component validation (invalid combinations)
- Impossible syllable structures

Previously split across test_rules.py and test_impossible_structures.py.
"""

import pytest
from app.spellcheck.engine import TibetanSpellChecker


# ============================================================================
# Pattern Checks (validation/pattern_checks.py)
# ============================================================================


class TestPatternChecks:
    """Test pattern-based validation (raw string, before parsing)"""

    def test_syllable_too_long(self):
        """Detect syllables with too many letters"""
        from app.spellcheck.validation import check_syllable_patterns

        # 8+ consecutive Tibetan letters is invalid (VBA line 122)
        too_long = "ཀཁགངཅཆཇཉ"  # 8 letters
        result = check_syllable_patterns(too_long)

        assert result is not None
        assert result["error_type"] == "syllable_too_long"
        assert result["severity"] == "error"

    def test_normal_length_syllable(self):
        """Normal syllables should pass"""
        from app.spellcheck.validation import check_syllable_patterns

        normal = "བོད"  # 3 letters
        result = check_syllable_patterns(normal)

        assert result is None  # No error

    def test_double_vowel_error(self):
        """Detect double vowel marks (invalid)"""
        from app.spellcheck.validation import check_syllable_patterns

        # Two vowel marks in sequence (from VBA line 243)
        double_vowel = "ཀིུ"  # ki + u (invalid)
        result = check_syllable_patterns(double_vowel)

        assert result is not None
        assert "vowel" in result["error_type"].lower()

    def test_encoding_error_detection(self):
        """Detect wrong Unicode characters"""
        from app.spellcheck.validation import check_syllable_patterns

        # Wrong 'a' character U+0FB0 instead of U+0F71 (from VBA line 790)
        wrong_unicode = "ཀ\u0fb0"  # Using wrong 'a'
        result = check_syllable_patterns(wrong_unicode)

        assert result is not None
        assert result["severity"] == "critical"  # Encoding errors are critical


# ============================================================================
# Component Validation (validation/validator.py)
# ============================================================================


class TestComponentValidation:
    """Test component-level validation against stacking rules"""

    def test_prefix_with_superscript(self):
        """Some prefixes can combine with superscripts"""
        from app.spellcheck.rules import validate_syllable_structure

        # Prefix + superscript + base (complex but valid)
        complex_valid = "བསྒྲུབ"  # ba + sa-mgo + grub
        result = validate_syllable_structure(complex_valid)

        # Should be valid or have specific rule
        assert result is None or result["severity"] != "error"

    def test_invalid_prefix_superscript_combo(self):
        """Invalid prefix + superscript combinations"""
        from app.spellcheck.rules import validate_syllable_structure

        # Made-up invalid combination
        invalid = "ལསྐ"  # la + ska (if invalid per rules)
        validate_syllable_structure(invalid)

        # Should detect if this combo is invalid
        # (Test depends on actual rules from VBA)

    def test_full_syllable_validation(self):
        """Test complete syllable validation"""
        from app.spellcheck.rules import validate_syllable_structure

        # Valid complex syllable
        valid = "སྐད"  # ska + da
        result = validate_syllable_structure(valid)
        assert result is None

        # Invalid syllable (made up)
        invalid = "ངསྐ"  # nga + ska (invalid if nga can't prefix)
        result = validate_syllable_structure(invalid)
        # Should return error if invalid


# NOTE: Sanskrit detection is deferred to Phase 3+
# See: docs/adr/SPELLCHECKER_DECISIONS.md (ADR-011)


# ============================================================================
# Impossible Structures (validation/completeness_checks.py)
# ============================================================================


@pytest.fixture(scope="module")
def engine():
    return TibetanSpellChecker()


# (syllable, error_type). The combined QA string is covered separately.
_IMPOSSIBLE_SYLLABLES = [
    ("ཨེརྡ", "consonant_after_vowel"),
    ("ཕ༹ཀལ", "unusual_mark_position"),
    ("ཨེཨོརོ", "multiple_vowels"),
    ("ེབ", "missing_root"),
    ("བྱབབ", "unparsed_characters"),
    ("བོདྡ", "consonant_after_vowel"),
    ("བོདབ", "unparsed_characters"),
    ("ཕ༹ཀ", "unusual_mark_position"),
    ("བ྄", "unparsed_characters"),
]


class TestImpossibleStructures:
    """Structurally impossible syllables, including the QA examples."""

    @pytest.mark.parametrize("syllable,expected_error_type", _IMPOSSIBLE_SYLLABLES)
    def test_syllable_error_type(self, engine, syllable, expected_error_type):
        error = engine.check_syllable(syllable)
        assert error is not None
        assert error["error_type"] == expected_error_type
        assert error["severity"] in ("error", "critical")

    def test_user_qa_input_all_invalid(self, engine):
        """ཨེརྡ་ཕ༹ཀལ་ཨེཨོརོ་ — each syllable is invalid."""
        errors = engine.check_text("ཨེརྡ་ཕ༹ཀལ་ཨེཨོརོ་")
        error_syllables = {e["word"] for e in errors if e["severity"] != "info"}
        assert {"ཨེརྡ", "ཕ༹ཀལ", "ཨེཨོརོ"} <= error_syllables
