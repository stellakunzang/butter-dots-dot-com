"""
Tests for Tibetan Syllable Splitting

Tests the splitting functions in splitter.py:
- split_syllables(): Split text by tsheg into syllable strings
- split_syllables_with_position(): Split with character position tracking

Previously part of test_syllable_parser.py.
"""
from app.spellcheck.splitter import split_syllables, split_syllables_with_position


class TestBasicSyllableSplitting:
    """Test basic syllable splitting by tsheg"""
    
    def test_split_by_tsheg(self):
        """Split text by tsheg (་) into syllables"""
        text = "བོད་ཡིག་"
        syllables = split_syllables(text)
        
        assert len(syllables) == 2
        assert syllables[0] == "བོད"
        assert syllables[1] == "ཡིག"
    
    def test_split_single_syllable(self):
        """Single syllable with no tsheg"""
        text = "བོད"
        syllables = split_syllables(text)
        
        assert len(syllables) == 1
        assert syllables[0] == "བོད"
    
    def test_split_with_trailing_tsheg(self):
        """Handle trailing tsheg correctly"""
        text = "བོད་ཡིག་"
        syllables = split_syllables(text)
        
        # Should not create empty syllable from trailing tsheg
        assert len(syllables) == 2
        assert "" not in syllables
    
    def test_split_multiple_syllables(self):
        """Split text with many syllables"""
        text = "བོད་ཀྱི་སྐད་ཡིག་"
        syllables = split_syllables(text)
        
        assert len(syllables) == 4
        assert syllables == ["བོད", "ཀྱི", "སྐད", "ཡིག"]


class TestPunctuationHandling:
    """Test handling of Tibetan punctuation"""
    
    def test_handle_shad(self):
        """Shad (།) as sentence delimiter"""
        text = "བོད་ཡིག་།"
        syllables = split_syllables(text)
        
        # Shad should separate but not be included as syllable
        assert len(syllables) == 2
        assert syllables == ["བོད", "ཡིག"]
        assert "།" not in syllables
    
    def test_handle_double_shad(self):
        """Double shad (༎) handling"""
        text = "བོད་ཡིག་༎"
        syllables = split_syllables(text)
        
        assert len(syllables) == 2
        assert "༎" not in syllables
    
    def test_multiple_sentences(self):
        """Multiple sentences separated by shad"""
        text = "བོད་ཡིག་། བོད་སྐད་།"
        syllables = split_syllables(text)
        
        # Should extract all syllables from both sentences
        assert "བོད" in syllables
        assert "ཡིག" in syllables
        assert "སྐད" in syllables


class TestPositionTracking:
    """Test syllable position tracking for error reporting"""
    
    def test_track_syllable_positions(self):
        """Track character position of each syllable"""
        text = "བོད་ཡིག་"
        result = split_syllables_with_position(text)
        
        assert len(result) == 2
        
        # First syllable "བོད" at position 0
        assert result[0]["syllable"] == "བོད"
        assert result[0]["position"] == 0
        
        # Second syllable "ཡིག" at position 4 (བོད + ་)
        assert result[1]["syllable"] == "ཡིག"
        assert isinstance(result[1]["position"], int)
        assert result[1]["position"] > 0
    
    def test_position_with_complex_text(self):
        """Position tracking in complex text"""
        text = "བོད་ཀྱི་སྐད་ཡིག་"
        result = split_syllables_with_position(text)
        
        # All syllables should have positions
        assert len(result) == 4
        for item in result:
            assert "syllable" in item
            assert "position" in item
            assert item["position"] >= 0
        
        # Positions should be increasing
        positions = [item["position"] for item in result]
        assert positions == sorted(positions)
    
    def test_position_after_punctuation(self):
        """Position tracking across punctuation"""
        text = "བོད་། ཡིག་"
        result = split_syllables_with_position(text)
        
        # Should track positions correctly even with punctuation
        assert len(result) >= 2
        assert all("position" in item for item in result)


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_string(self):
        """Empty string returns empty list"""
        assert split_syllables("") == []
    
    def test_whitespace_only(self):
        """Whitespace-only string returns empty list"""
        assert split_syllables("   ") == []
        assert split_syllables("\t\n") == []
    
    def test_only_tsheg(self):
        """String of only tsheg returns empty list"""
        assert split_syllables("་་་") == []
    
    def test_mixed_whitespace_and_tibetan(self):
        """Handle mixed whitespace and Tibetan"""
        text = "  བོད་  ཡིག་  "
        syllables = split_syllables(text)
        
        # Should extract syllables, ignore whitespace
        assert "བོད" in syllables
        assert "ཡིག" in syllables
    
    def test_consecutive_tsheg(self):
        """Handle consecutive tsheg (edge case)"""
        text = "བོད་་ཡིག"  # Double tsheg (unusual but possible)
        syllables = split_syllables(text)
        
        # Should not create empty syllables
        assert "" not in syllables
        assert len([s for s in syllables if s]) == 2


class TestComplexStructures:
    """Test complex Tibetan structures stay together during splitting"""
    
    def test_syllable_with_stacking(self):
        """Syllables with subscripts/superscripts"""
        text = "སྐད་བརྒྱུད་"
        syllables = split_syllables(text)
        
        # Complex stacking should stay together as syllables
        assert len(syllables) == 2
        assert "སྐད" in syllables  # sa + ka + da (with subscript)
        assert "བརྒྱུད" in syllables  # complex stacking
    
    def test_syllable_with_vowels(self):
        """Syllables with vowel marks"""
        text = "རྒྱལ་པོ་"
        syllables = split_syllables(text)
        
        # Vowel marks should stay with their syllables
        assert len(syllables) == 2
        assert "རྒྱལ" in syllables
        assert "པོ" in syllables
    
    def test_preserves_syllable_integrity(self):
        """Syllables should not be broken apart"""
        text = "སྤྱན་རས་གཟིགས་"
        syllables = split_syllables(text)
        
        # Each syllable should be complete
        for syllable in syllables:
            # Should have at least a base consonant
            assert len(syllable) > 0
            # Should be valid Tibetan
            assert any('\u0F40' <= c <= '\u0FBC' for c in syllable)
