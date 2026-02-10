"""
Tests for Tibetan spelling rules validation

Based on traditional Tibetan grammar rules and linguistic research
Following TDD: Write tests FIRST, then implement
"""
import pytest


class TestPrefixRules:
    """Test prefix validation rules"""
    
    def test_valid_prefixes_exist(self):
        """Only 5 letters can be prefixes: ga, da, ba, ma, ra"""
        from app.spellcheck.rules import VALID_PREFIXES
        
        # These are the only valid prefixes in Tibetan
        assert len(VALID_PREFIXES) == 5
        assert "ག" in VALID_PREFIXES  # ga
        assert "ད" in VALID_PREFIXES  # da
        assert "བ" in VALID_PREFIXES  # ba
        assert "མ" in VALID_PREFIXES  # ma
        assert "ར" in VALID_PREFIXES  # ra
    
    def test_ga_prefix_valid_combinations(self):
        """ga (ག) can prefix certain letters"""
        from app.spellcheck.rules import is_valid_prefix_combination
        
        # Valid combinations (from VBA research)
        assert is_valid_prefix_combination("ག", "ཡ") is True  # ga-ya
        assert is_valid_prefix_combination("ག", "ཉ") is True  # ga-nya
        assert is_valid_prefix_combination("ག", "ད") is True  # ga-da
        assert is_valid_prefix_combination("ག", "ང") is True  # ga-nga VALID
        
        # Invalid combinations (from VBA line 334)
        # ga CANNOT prefix: ka, kha, cha, ja, tha, tsa, pa, pha, dza, wa, ha
        assert is_valid_prefix_combination("ག", "ཀ") is False  # ga-ka invalid
        assert is_valid_prefix_combination("ག", "པ") is False  # ga-pa invalid
    
    def test_da_prefix_valid_combinations(self):
        """da (ད) can prefix certain letters"""
        from app.spellcheck.rules import is_valid_prefix_combination
        
        # Valid combinations
        assert is_valid_prefix_combination("ད", "ཀ") is True  # da-ka
        assert is_valid_prefix_combination("ད", "ག") is True  # da-ga
        
        # Invalid combinations (from VBA line 334)
        assert is_valid_prefix_combination("ད", "ང") is False  # da-nga invalid
    
    def test_non_prefix_letter(self):
        """Letters that are not prefixes should fail"""
        from app.spellcheck.rules import is_valid_prefix_combination
        
        # la (ལ) is NOT a valid prefix
        assert is_valid_prefix_combination("ལ", "ཀ") is False
        assert is_valid_prefix_combination("ས", "ཀ") is False  # sa not a prefix
    
    def test_prefix_with_empty_base(self):
        """Prefix with empty base should be invalid"""
        from app.spellcheck.rules import is_valid_prefix_combination
        
        assert is_valid_prefix_combination("ག", "") is False
        assert is_valid_prefix_combination("", "ཀ") is False


class TestSuperscriptRules:
    """Test superscript (ra-mgo, la-mgo, sa-mgo) validation"""
    
    def test_valid_superscripts_exist(self):
        """Only 3 letters can be superscripts"""
        from app.spellcheck.rules import VALID_SUPERSCRIPTS
        
        assert len(VALID_SUPERSCRIPTS) == 3
        assert "ར" in VALID_SUPERSCRIPTS  # ra-mgo
        assert "ལ" in VALID_SUPERSCRIPTS  # la-mgo  
        assert "ས" in VALID_SUPERSCRIPTS  # sa-mgo
    
    def test_ra_mgo_valid_combinations(self):
        """ra-mgo (ར) can superscript certain letters"""
        from app.spellcheck.rules import is_valid_superscript_combination
        
        # Valid combinations (from authoritative valid stacks list)
        assert is_valid_superscript_combination("ར", "ཀ") is True  # རྐ rka
        assert is_valid_superscript_combination("ར", "ག") is True  # རྒ rga
        assert is_valid_superscript_combination("ར", "ང") is True  # རྔ rnga - VALID per stacks list
        
        # Invalid combinations (not in valid stacks list)
        # TODO: Add examples of invalid ra-mgo combinations
    
    def test_la_mgo_valid_combinations(self):
        """la-mgo (ལ) can superscript certain letters"""
        from app.spellcheck.rules import is_valid_superscript_combination
        
        # Valid combinations (from authoritative valid stacks list)
        assert is_valid_superscript_combination("ལ", "ཀ") is True  # ལྐ lka
        assert is_valid_superscript_combination("ལ", "ག") is True  # ལྒ lga
        assert is_valid_superscript_combination("ལ", "ང") is True  # ལྔ lnga - VALID per stacks list
        
        # Invalid combinations (not in valid stacks list)
        # TODO: Add examples of invalid la-mgo combinations
    
    def test_sa_mgo_valid_combinations(self):
        """sa-mgo (ས) can superscript certain letters"""
        from app.spellcheck.rules import is_valid_superscript_combination
        
        # Valid combinations (from authoritative valid stacks list)
        assert is_valid_superscript_combination("ས", "ཀ") is True  # སྐ ska
        assert is_valid_superscript_combination("ས", "ག") is True  # སྒ sga
        assert is_valid_superscript_combination("ས", "ང") is True  # སྔ snga - VALID per stacks list
        
        # Invalid combinations (not in valid stacks list)
        # TODO: Add examples of invalid sa-mgo combinations
    
    def test_non_superscript_letter(self):
        """Non-superscript letters should fail"""
        from app.spellcheck.rules import is_valid_superscript_combination
        
        # ga (ག) cannot be a superscript
        assert is_valid_superscript_combination("ག", "ཀ") is False


class TestSubscriptRules:
    """Test subscript (ya-btags, ra-btags, la-btags, wa-zur) validation"""
    
    def test_valid_subscripts_exist(self):
        """Only 4 letters can be subscripts"""
        from app.spellcheck.rules import VALID_SUBSCRIPTS
        
        assert len(VALID_SUBSCRIPTS) == 4
        assert "\u0FB1" in VALID_SUBSCRIPTS  # ya-btags (U+0FB1)
        assert "\u0FB2" in VALID_SUBSCRIPTS  # ra-btags (U+0FB2)
        assert "\u0FB3" in VALID_SUBSCRIPTS  # la-btags (U+0FB3)
        assert "\u0FAD" in VALID_SUBSCRIPTS  # wa-zur (U+0FAD)
    
    def test_ya_btags_valid_combinations(self):
        """ya-btags (U+0FB1) can subscript certain letters"""
        from app.spellcheck.rules import is_valid_subscript_combination
        
        # ya-btags = \u0FB1 (subscript ya) - combines like: ཀྱ (kya)
        # Valid combinations (from VBA line 578)
        assert is_valid_subscript_combination("ཀ", "\u0FB1") is True  # ka + ya = ཀྱ (kya)
        assert is_valid_subscript_combination("ག", "\u0FB1") is True  # ga + ya = གྱ (gya)
        
        # Invalid combinations (from VBA line 578) 
        assert is_valid_subscript_combination("ང", "\u0FB1") is False  # nga + ya invalid
    
    def test_ra_btags_valid_combinations(self):
        """ra-btags (U+0FB2) can subscript certain letters"""
        from app.spellcheck.rules import is_valid_subscript_combination
        
        # ra-btags = \u0FB2 (subscript ra) - combines like: ཀྲ (kra)
        # Valid combinations (from VBA line 608)
        assert is_valid_subscript_combination("ཀ", "\u0FB2") is True  # ka + ra = ཀྲ (kra)
        assert is_valid_subscript_combination("ག", "\u0FB2") is True  # ga + ra = གྲ (gra)
        
        # Invalid combinations
        assert is_valid_subscript_combination("ང", "\u0FB2") is False  # nga + ra invalid
    
    def test_la_btags_valid_combinations(self):
        """la-btags (U+0FB3) can subscript certain letters"""
        from app.spellcheck.rules import is_valid_subscript_combination
        
        # la-btags = \u0FB3 (subscript la) - combines like: ཀླ (kla)
        # Valid combinations (from VBA line 638)
        assert is_valid_subscript_combination("ཀ", "\u0FB3") is True  # ka + la = ཀླ (kla)
        assert is_valid_subscript_combination("ག", "\u0FB3") is True  # ga + la = གླ (gla)
        
        # Invalid combinations
        assert is_valid_subscript_combination("ང", "\u0FB3") is False  # nga + la invalid
    
    def test_wa_zur_valid_combinations(self):
        """wa-zur (U+0FAD) can subscript certain letters"""
        from app.spellcheck.rules import is_valid_subscript_combination
        
        # wa-zur = \u0FAD (subscript wa) - combines like: ཀྭ (kwa)
        # Valid combinations (from VBA line 668)
        assert is_valid_subscript_combination("ཀ", "\u0FAD") is True  # ka + wa = ཀྭ (kwa)
        assert is_valid_subscript_combination("ག", "\u0FAD") is True  # ga + wa = གྭ (gwa)
        
        # Invalid combinations
        assert is_valid_subscript_combination("ང", "\u0FAD") is False  # nga + wa invalid


class TestPatternRules:
    """Test pattern-based validation (from VBA regex patterns)"""
    
    def test_syllable_too_long(self):
        """Detect syllables with too many letters"""
        from app.spellcheck.rules import check_syllable_patterns
        
        # 8+ consecutive Tibetan letters is invalid (VBA line 122)
        too_long = "ཀཁགངཅཆཇཉ"  # 8 letters
        result = check_syllable_patterns(too_long)
        
        assert result is not None
        assert result["error_type"] == "syllable_too_long"
        assert result["severity"] == "error"
    
    def test_normal_length_syllable(self):
        """Normal syllables should pass"""
        from app.spellcheck.rules import check_syllable_patterns
        
        normal = "བོད"  # 3 letters
        result = check_syllable_patterns(normal)
        
        assert result is None  # No error
    
    def test_double_vowel_error(self):
        """Detect double vowel marks (invalid)"""
        from app.spellcheck.rules import check_syllable_patterns
        
        # Two vowel marks in sequence (from VBA line 243)
        double_vowel = "ཀིུ"  # ki + u (invalid)
        result = check_syllable_patterns(double_vowel)
        
        assert result is not None
        assert "vowel" in result["error_type"].lower()
    
    def test_encoding_error_detection(self):
        """Detect wrong Unicode characters"""
        from app.spellcheck.rules import check_syllable_patterns
        
        # Wrong 'a' character U+0FB0 instead of U+0F71 (from VBA line 790)
        wrong_unicode = "ཀ\u0FB0"  # Using wrong 'a'
        result = check_syllable_patterns(wrong_unicode)
        
        assert result is not None
        assert result["severity"] == "critical"  # Encoding errors are critical


# NOTE: Sanskrit detection is OUT OF SCOPE for MVP (Phase 1)
# See: docs/planning/MVP_SCOPE.md and docs/adr/SPELLCHECKER_DECISIONS.md (ADR-011)
# Sanskrit validation is deferred to Phase 3+


class TestComplexRules:
    """Test complex multi-part rules"""
    
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


class TestRuleHelpers:
    """Test helper functions"""
    
    def test_get_syllable_components(self):
        """Parse syllable into components"""
        from app.spellcheck.rules import parse_syllable_structure
        
        # Simple syllable
        simple = "ཀ"
        components = parse_syllable_structure(simple)
        assert components["base"] == "ཀ"
        assert components["prefix"] is None
        
        # With prefix
        with_prefix = "གཡ"  # ga + ya
        components = parse_syllable_structure(with_prefix)
        assert components["prefix"] == "ག"
        assert components["base"] == "ཡ"
        
        # With subscript
        with_subscript = "ཀྱ"  # kya
        components = parse_syllable_structure(with_subscript)
        assert components["base"] == "ཀ"
        assert components["subscript"] == "ྱ"
    
    def test_error_severity_mapping(self):
        """Error types map to correct severity"""
        from app.spellcheck.rules import get_error_severity
        
        assert get_error_severity("encoding_error") == "critical"
        assert get_error_severity("invalid_prefix") == "error"
        assert get_error_severity("sanskrit_marker") == "info"
