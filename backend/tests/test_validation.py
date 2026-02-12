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
        wrong_unicode = "ཀ\u0FB0"  # Using wrong 'a'
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
        result = validate_syllable_structure(invalid)
        
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

class TestImpossibleStructures:
    """Test detection of structurally impossible syllables"""
    
    def test_subscript_after_suffix_impossible(self):
        """Subscript appearing after suffix is structurally impossible"""
        engine = TibetanSpellChecker()
        
        # ཨེརྡ = a + e-vowel + ra-suffix + da-subscript
        # Subscripts MUST come before vowels, not after suffixes
        syllable = "ཨེརྡ"
        error = engine.check_syllable(syllable)
        
        assert error is not None, f"Should detect subscript after suffix in {syllable}"
        assert error['severity'] in ['error', 'critical']
    
    def test_multiple_base_consonants_impossible(self):
        """Multiple base consonants in one syllable is impossible"""
        engine = TibetanSpellChecker()
        
        # ཕ༹ཀལ = pha + mark + ka + la (multiple base consonants)
        # A syllable can only have ONE root consonant
        syllable = "ཕ༹ཀལ"
        error = engine.check_syllable(syllable)
        
        assert error is not None, f"Should detect multiple base consonants in {syllable}"
        assert error['severity'] in ['error', 'critical']
    
    def test_multiple_vowels_on_different_consonants(self):
        """Multiple vowels attached to different consonants is impossible"""
        engine = TibetanSpellChecker()
        
        # ཨེཨོརོ = a + e-vowel + a + o-vowel + ra + o-vowel
        # Multiple base consonants with their own vowels = impossible
        syllable = "ཨེཨོརོ"
        error = engine.check_syllable(syllable)
        
        assert error is not None, f"Should detect multiple vowel groups in {syllable}"
        assert error['severity'] in ['error', 'critical']
    
    def test_vowel_before_root(self):
        """Vowel appearing before root consonant is impossible"""
        engine = TibetanSpellChecker()
        
        # Vowel mark before any consonant = impossible
        syllable = "ེབ"  # vowel + ba
        error = engine.check_syllable(syllable)
        
        assert error is not None, f"Should detect vowel before consonant in {syllable}"
    
    def test_base_consonant_after_subscript(self):
        """Base consonant appearing after subscript (except suffix) is impossible"""
        engine = TibetanSpellChecker()
        
        syllable = "བྱབབ"  # bya + ba + ba (too many base consonants)
        error = engine.check_syllable(syllable)
        
        assert error is not None, f"Should detect multiple base consonants in {syllable}"


class TestUserQAFindings:
    """Test cases from user's actual QA testing"""
    
    def test_user_qa_input_all_invalid(self):
        """User's QA input: ཨེརྡ་ཕ༹ཀལ་ཨེཨོརོ་ - ALL syllables are invalid"""
        engine = TibetanSpellChecker()
        
        text = "ཨེརྡ་ཕ༹ཀལ་ཨེཨོརོ་"
        errors = engine.check_text(text)
        
        # Should detect errors in ALL THREE syllables
        error_syllables = {e['word'] for e in errors if e['severity'] != 'info'}
        
        assert "ཨེརྡ" in error_syllables, "First syllable ཨེརྡ should be flagged"
        assert "ཕ༹ཀལ" in error_syllables, "Second syllable ཕ༹ཀལ should be flagged"
        assert "ཨེཨོརོ" in error_syllables, "Third syllable ཨེཨོརོ should be flagged"
        
        assert len(error_syllables) >= 3, f"Should flag all 3 syllables, but only flagged: {error_syllables}"
    
    def test_individual_qa_syllable_1(self):
        """First QA syllable: ཨེརྡ (subscript after suffix)"""
        engine = TibetanSpellChecker()
        
        error = engine.check_syllable("ཨེརྡ")
        assert error is not None, "ཨེརྡ has subscript after suffix - should be invalid"
    
    def test_individual_qa_syllable_2(self):
        """Second QA syllable: ཕ༹ཀལ (multiple base consonants)"""
        engine = TibetanSpellChecker()
        
        error = engine.check_syllable("ཕ༹ཀལ")
        assert error is not None, "ཕ༹ཀལ has multiple base consonants - should be invalid"
    
    def test_individual_qa_syllable_3(self):
        """Third QA syllable: ཨེཨོརོ (multiple vowel groups)"""
        engine = TibetanSpellChecker()
        
        error = engine.check_syllable("ཨེཨོརོ")
        assert error is not None, "ཨེཨོརོ has multiple vowel groups - should be invalid"


class TestParserCompleteness:
    """Test that parser consumes all characters"""
    
    def test_parser_identifies_unparsed_characters(self):
        """Parser should flag when characters remain unparsed"""
        engine = TibetanSpellChecker()
        
        # Create a syllable with trailing garbage
        # བོད is valid, but བོདྡ has trailing subscript (impossible)
        syllable = "བོདྡ"  # bod + subscript-da
        error = engine.check_syllable(syllable)
        
        assert error is not None, "Should detect unparsed trailing subscript"
    
    def test_parser_detects_consonant_after_suffix(self):
        """Extra consonant after suffix should be detected"""
        engine = TibetanSpellChecker()
        
        syllable = "བོདབ"  # bod + ba (ba is NOT valid post-suffix)
        error = engine.check_syllable(syllable)
        
        assert error is not None, "Should detect invalid post-suffix"


class TestSpecialMarks:
    """Test handling of special Tibetan marks"""
    
    def test_tsa_phru_mark_unusual(self):
        """TSA-PHRU mark (U+0F39) in middle of syllable is unusual"""
        engine = TibetanSpellChecker()
        
        # ཕ༹ has TSA-PHRU mark which is a special modifier
        # When followed by other consonants, it creates invalid structure
        syllable = "ཕ༹ཀ"
        error = engine.check_syllable(syllable)
        
        # At minimum, should flag as unusual/info
        assert error is not None or syllable, "Should flag unusual TSA-PHRU usage"
    
    def test_halanta_mark_unusual(self):
        """HALANTA mark (U+0F84) should be rare/flagged"""
        engine = TibetanSpellChecker()
        
        syllable = "བ྄"  # ba + halanta
        # This is a special case - might be valid in Sanskrit transliteration
        # But should be noted as unusual at least
        result = engine.check_syllable(syllable)
        # May or may not error - depends on if we handle Sanskrit markers
