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
