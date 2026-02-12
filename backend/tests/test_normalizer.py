"""
Tests for Tibetan Unicode normalization

Following TDD: Write tests FIRST, then implement
"""
import pytest


class TestUnicodeNormalization:
    """Test Unicode normalization to NFC form"""
    
    def test_normalize_to_nfc(self):
        """Text should be normalized to NFC (composed) form"""
        from app.spellcheck.normalizer import normalize_tibetan
        
        # Tibetan syllable "sku" - same visual, different Unicode representations
        # These should normalize to the same string
        nfc_form = "སྐུ"  # Already NFC
        nfd_form = "སྐུ"  # NFD (decomposed)
        
        assert normalize_tibetan(nfc_form) == normalize_tibetan(nfd_form)
        assert normalize_tibetan(nfc_form) == nfc_form  # Should stay NFC
    
    def test_remove_zero_width_spaces(self):
        """Remove zero-width spaces, joiners, and non-joiners"""
        from app.spellcheck.normalizer import normalize_tibetan
        
        # Zero-width space (U+200B)
        text_with_zwsp = "བོད\u200bཡིག"
        assert normalize_tibetan(text_with_zwsp) == "བོདཡིག"
        
        # Zero-width non-joiner (U+200C)
        text_with_zwnj = "བོད\u200cཡིག"
        assert normalize_tibetan(text_with_zwnj) == "བོདཡིག"
        
        # Zero-width joiner (U+200D)
        text_with_zwj = "བོད\u200dཡིག"
        assert normalize_tibetan(text_with_zwj) == "བོདཡིག"
    
    def test_normalize_empty_string(self):
        """Empty string should return empty string"""
        from app.spellcheck.normalizer import normalize_tibetan
        
        assert normalize_tibetan("") == ""
        assert normalize_tibetan("   ") == "   "  # Whitespace preserved
    
    def test_normalize_mixed_script(self):
        """Text with Tibetan and other scripts normalizes correctly"""
        from app.spellcheck.normalizer import normalize_tibetan
        
        mixed = "བོད་ (Tibetan) ཡིག"
        result = normalize_tibetan(mixed)
        assert "བོད" in result
        assert "Tibetan" in result  # Non-Tibetan preserved


class TestTibetanCharacterValidation:
    """Test Tibetan character validation"""
    
    def test_is_tibetan_consonant(self):
        """Tibetan consonants should be identified"""
        from app.spellcheck.normalizer import is_tibetan_char
        
        assert is_tibetan_char("ལ") is True  # la
        assert is_tibetan_char("བ") is True  # ba
        assert is_tibetan_char("ག") is True  # ga
        assert is_tibetan_char("ད") is True  # da
    
    def test_is_tibetan_vowel(self):
        """Tibetan vowel marks should be identified"""
        from app.spellcheck.normalizer import is_tibetan_char
        
        assert is_tibetan_char("ི") is True  # gi-gu (vowel i)
        assert is_tibetan_char("ུ") is True  # zhabs-kyu (vowel u)
        assert is_tibetan_char("ེ") is True  # 'greng-bu (vowel e)
    
    def test_is_tibetan_punctuation(self):
        """Tibetan punctuation should be identified"""
        from app.spellcheck.normalizer import is_tibetan_char
        
        assert is_tibetan_char("་") is True  # tsheg (syllable separator)
        assert is_tibetan_char("།") is True  # shad (sentence ender)
        assert is_tibetan_char("༎") is True  # double shad
    
    def test_is_not_tibetan(self):
        """Non-Tibetan characters should be rejected"""
        from app.spellcheck.normalizer import is_tibetan_char
        
        assert is_tibetan_char("a") is False  # Latin
        assert is_tibetan_char("1") is False  # Number
        assert is_tibetan_char("་") is True   # Tibetan tsheg
        assert is_tibetan_char("") is False   # Empty string
        assert is_tibetan_char(" ") is False  # Space (not Tibetan range)
    
    def test_is_tibetan_subscript(self):
        """Tibetan subscripts should be identified"""
        from app.spellcheck.normalizer import is_tibetan_char
        
        assert is_tibetan_char("ྱ") is True  # ya-btags (subscript ya)
        assert is_tibetan_char("ྲ") is True  # ra-btags (subscript ra)
        assert is_tibetan_char("ླ") is True  # la-btags (subscript la)
        assert is_tibetan_char("ྭ") is True  # wa-zur (subscript wa)


class TestNormalizeTibetanWithPositionMap:
    """Test normalize_tibetan_with_position_map returns correct position mapping."""

    def test_empty_string(self):
        from app.spellcheck.normalizer import normalize_tibetan_with_position_map

        text, pos_map = normalize_tibetan_with_position_map("")
        assert text == ""
        assert pos_map == []

    def test_no_zero_width_chars(self):
        """Plain Tibetan text: normalized positions equal original positions."""
        from app.spellcheck.normalizer import normalize_tibetan_with_position_map

        original = "བོད་ཡིག"
        text, pos_map = normalize_tibetan_with_position_map(original)
        assert text == original
        assert pos_map == list(range(len(original)))

    def test_single_zero_width_space(self):
        """One ZWSP between syllables should shift all subsequent positions."""
        from app.spellcheck.normalizer import normalize_tibetan_with_position_map

        #              0  1  2  3     4  5  6
        original = "བོད\u200bཡིག"  # ZWSP at index 3
        text, pos_map = normalize_tibetan_with_position_map(original)
        assert text == "བོདཡིག"
        # pos_map should map back through the removed ZWSP:
        # normalized[0]='བ'→orig 0, [1]='ོ'→1, [2]='ད'→2,
        # normalized[3]='ཡ'→orig 4 (skipped ZWSP at 3), [4]='ི'→5, [5]='ག'→6
        assert pos_map == [0, 1, 2, 4, 5, 6]

    def test_multiple_zero_width_chars(self):
        """Several zero-width chars accumulate offset correctly."""
        from app.spellcheck.normalizer import normalize_tibetan_with_position_map

        #               0  1     2  3     4
        original = "ཀ\u200bག\u200cང"
        text, pos_map = normalize_tibetan_with_position_map(original)
        assert text == "ཀགང"
        assert pos_map == [0, 2, 4]

    def test_consecutive_zero_width_chars(self):
        """Two zero-width chars in a row."""
        from app.spellcheck.normalizer import normalize_tibetan_with_position_map

        #               0     1     2  3
        original = "ཀ\u200b\u200dག"
        text, pos_map = normalize_tibetan_with_position_map(original)
        assert text == "ཀག"
        assert pos_map == [0, 3]

    def test_leading_zero_width(self):
        """Zero-width char at the very start of text."""
        from app.spellcheck.normalizer import normalize_tibetan_with_position_map

        original = "\u200bཀ"
        text, pos_map = normalize_tibetan_with_position_map(original)
        assert text == "ཀ"
        assert pos_map == [1]

    def test_agrees_with_normalize_tibetan(self):
        """Result text must always equal normalize_tibetan(original)."""
        from app.spellcheck.normalizer import normalize_tibetan, normalize_tibetan_with_position_map

        samples = [
            "བོད་ཡིག",
            "བོད\u200bཡིག",
            "\u200cབོད\u200dཡིག\u200b",
            "",
        ]
        for sample in samples:
            text, _ = normalize_tibetan_with_position_map(sample)
            assert text == normalize_tibetan(sample), f"Mismatch for {sample!r}"


class TestTextCleaning:
    """Test text cleaning utilities"""
    
    def test_strip_non_tibetan(self):
        """Extract only Tibetan characters from mixed text"""
        from app.spellcheck.normalizer import extract_tibetan
        
        mixed = "བོད་ཡིག་ (Tibetan script) བོད་སྐད་"
        result = extract_tibetan(mixed)
        
        # Should keep Tibetan, remove Latin/punctuation
        assert "བོད" in result
        assert "ཡིག" in result
        assert "Tibetan" not in result
        assert "(" not in result
    
    def test_extract_tibetan_from_empty(self):
        """Extracting from empty string returns empty"""
        from app.spellcheck.normalizer import extract_tibetan
        
        assert extract_tibetan("") == ""
        assert extract_tibetan("English only") == ""
    
    def test_extract_preserves_tibetan_structure(self):
        """Tibetan structure (tsheg, etc) should be preserved"""
        from app.spellcheck.normalizer import extract_tibetan
        
        text = "བོད་ཡིག་"
        result = extract_tibetan(text)
        
        assert result == "བོད་ཡིག་"
        assert "་" in result  # tsheg preserved
