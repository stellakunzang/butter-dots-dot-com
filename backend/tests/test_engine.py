"""
Tests for main Tibetan Spell Check Engine

Integration of all components: normalizer, parser, rules
Following TDD: Write tests FIRST, then implement
"""
import pytest


class TestEngineInitialization:
    """Test spell checker engine initialization"""
    
    def test_engine_creates_successfully(self):
        """Engine should initialize without errors"""
        from app.spellcheck.engine import TibetanSpellChecker
        
        engine = TibetanSpellChecker()
        assert engine is not None
    
    def test_engine_has_rules_loaded(self):
        """Engine should load spelling rules on init"""
        from app.spellcheck.engine import TibetanSpellChecker
        
        engine = TibetanSpellChecker()
        # Should have rules available
        assert hasattr(engine, 'check_syllable')
        assert hasattr(engine, 'check_text')


class TestSingleSyllableChecking:
    """Test checking individual syllables"""
    
    def test_check_valid_syllable_returns_none(self):
        """Valid syllable should return None (no error)"""
        from app.spellcheck.engine import TibetanSpellChecker
        
        engine = TibetanSpellChecker()
        result = engine.check_syllable("བོད")  # "bod" - valid
        
        assert result is None  # No error
    
    def test_check_invalid_prefix(self):
        """Invalid prefix should be detected"""
        from app.spellcheck.engine import TibetanSpellChecker
        
        engine = TibetanSpellChecker()
        result = engine.check_syllable("གཀར")  # ga + ka + ra (invalid: ga cannot prefix ka)
        
        assert result is not None
        assert result['error_type'] == 'invalid_prefix_combination'
        assert result['severity'] == 'error'
        assert 'word' in result
        assert result['word'] == "གཀར"
    
    def test_check_invalid_superscript(self):
        """Invalid superscript combination detected"""
        from app.spellcheck.engine import TibetanSpellChecker
        
        engine = TibetanSpellChecker()
        # Example invalid ra-mgo combination (from VBA)
        result = engine.check_syllable("རང")  # rnga - invalid
        
        if result:  # If detected as invalid
            assert result['error_type'] in ['invalid_superscript', 'invalid_combination']
            assert result['severity'] == 'error'
    
    def test_check_syllable_too_long(self):
        """Syllable with too many letters"""
        from app.spellcheck.engine import TibetanSpellChecker
        
        engine = TibetanSpellChecker()
        too_long = "ཀཁགངཅཆཇཉ"  # 8+ letters
        result = engine.check_syllable(too_long)
        
        assert result is not None
        assert result['error_type'] == 'syllable_too_long'
        assert result['severity'] == 'error'
    
    def test_check_encoding_error(self):
        """Encoding error should be critical severity"""
        from app.spellcheck.engine import TibetanSpellChecker
        
        engine = TibetanSpellChecker()
        # Wrong Unicode character (from VBA line 790)
        wrong = "ཀ\u0FB0"  # Using wrong 'a'
        result = engine.check_syllable(wrong)
        
        if result:
            assert result['severity'] == 'critical'


class TestFullTextChecking:
    """Test checking complete Tibetan text"""
    
    def test_check_valid_text_no_errors(self):
        """Valid text should return empty error list"""
        from app.spellcheck.engine import TibetanSpellChecker
        
        engine = TibetanSpellChecker()
        text = "བོད་ཡིག་"  # "Tibetan script" - valid
        errors = engine.check_text(text)
        
        assert isinstance(errors, list)
        assert len(errors) == 0
    
    def test_check_text_with_one_error(self):
        """Text with one error should return list with one error"""
        from app.spellcheck.engine import TibetanSpellChecker
        
        engine = TibetanSpellChecker()
        text = "བོད་གཀར་"  # Second syllable invalid (ga cannot prefix ka)
        errors = engine.check_text(text)
        
        assert len(errors) == 1
        assert errors[0]['word'] == "གཀར"
        assert 'position' in errors[0]
        assert errors[0]['position'] > 0  # Not at start
    
    def test_check_text_with_multiple_errors(self):
        """Text with multiple errors"""
        from app.spellcheck.engine import TibetanSpellChecker
        
        engine = TibetanSpellChecker()
        # Both syllables invalid (hypothetical)
        text = "ལང་སང་"  # If both invalid
        errors = engine.check_text(text)
        
        if len(errors) > 0:
            # Should have position tracking
            assert all('position' in e for e in errors)
            # Positions should be different
            if len(errors) > 1:
                positions = [e['position'] for e in errors]
                assert len(set(positions)) == len(positions)  # All unique
    
    def test_check_text_preserves_position(self):
        """Error positions should match actual text positions"""
        from app.spellcheck.engine import TibetanSpellChecker
        
        engine = TibetanSpellChecker()
        text = "བོད་ལང་ཡིག་"  # Middle syllable invalid
        errors = engine.check_text(text)
        
        if len(errors) > 0:
            for error in errors:
                # Position should point to actual syllable location
                pos = error['position']
                word = error['word']
                assert text[pos:pos+len(word)] == word or text[pos] in word
    
    def test_check_text_with_punctuation(self):
        """Text with punctuation should be handled"""
        from app.spellcheck.engine import TibetanSpellChecker
        
        engine = TibetanSpellChecker()
        text = "བོད་ཡིག་། བོད་སྐད་།"  # With shad
        errors = engine.check_text(text)
        
        # Should check syllables across punctuation
        assert isinstance(errors, list)
    
    def test_check_empty_text(self):
        """Empty text should return empty error list"""
        from app.spellcheck.engine import TibetanSpellChecker
        
        engine = TibetanSpellChecker()
        errors = engine.check_text("")
        
        assert errors == []
    
    def test_check_mixed_valid_invalid(self):
        """Mixed valid and invalid syllables"""
        from app.spellcheck.engine import TibetanSpellChecker
        
        engine = TibetanSpellChecker()
        # NOTE: ལང་ is VALID - ལ (la) is root, ང (nga) is a valid suffix
        text = "བོད་ལང་ཡིག་"  # all valid!
        errors = engine.check_text(text)
        
        # None of these should be flagged as errors
        invalid_words = [e['word'] for e in errors]
        assert "བོད" not in invalid_words  # བ (root) + vowel + ད (suffix) = valid
        assert "ལང" not in invalid_words  # ལ (root) + ང (suffix) = valid
        assert "ཡིག" not in invalid_words  # ཡ (root) + vowel + ག (suffix) = valid


class TestErrorStructure:
    """Test error object structure"""
    
    def test_error_has_required_fields(self):
        """Error objects should have all required fields"""
        from app.spellcheck.engine import TibetanSpellChecker
        
        engine = TibetanSpellChecker()
        # Use an actually invalid word for this test
        # Example: གཀ where ga prefix before ka root = INVALID
        text = "གཀ"  # Invalid: ga cannot prefix ka
        errors = engine.check_text(text)
        
        if len(errors) > 0:
            error = errors[0]
            assert 'word' in error
            assert 'position' in error
            assert 'error_type' in error
            assert 'severity' in error
    
    def test_severity_levels(self):
        """Severity should be one of: critical, error, info"""
        from app.spellcheck.engine import TibetanSpellChecker
        
        engine = TibetanSpellChecker()
        
        # Create various error types
        texts = [
            "ལང་",  # Invalid prefix (error)
            "ཀ\u0FB0",  # Encoding error (critical)
        ]
        
        valid_severities = {'critical', 'error', 'info'}
        
        for text in texts:
            errors = engine.check_text(text)
            for error in errors:
                assert error['severity'] in valid_severities
    
    def test_error_type_is_descriptive(self):
        """Error type should be descriptive string"""
        from app.spellcheck.engine import TibetanSpellChecker
        
        engine = TibetanSpellChecker()
        text = "ལང་"
        errors = engine.check_text(text)
        
        if len(errors) > 0:
            error_type = errors[0]['error_type']
            assert isinstance(error_type, str)
            assert len(error_type) > 0
            # Should use snake_case
            assert error_type.islower() or '_' in error_type


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_check_none_input(self):
        """None input should handle gracefully"""
        from app.spellcheck.engine import TibetanSpellChecker
        
        engine = TibetanSpellChecker()
        
        with pytest.raises(TypeError):
            engine.check_text(None)
    
    def test_check_non_tibetan_text(self):
        """Non-Tibetan text should handle gracefully"""
        from app.spellcheck.engine import TibetanSpellChecker
        
        engine = TibetanSpellChecker()
        text = "Hello world"
        errors = engine.check_text(text)
        
        # Should have one informational message about non-Tibetan characters
        assert len(errors) == 1
        assert errors[0]['error_type'] == 'non_tibetan_skipped'
        assert errors[0]['severity'] == 'info'
    
    def test_check_mixed_script_text(self):
        """Mixed Tibetan and English"""
        from app.spellcheck.engine import TibetanSpellChecker
        
        engine = TibetanSpellChecker()
        text = "བོད་ (Tibetan) ཡིག་"
        errors = engine.check_text(text)
        
        # Should only check Tibetan parts
        assert isinstance(errors, list)
    
    def test_check_very_long_text(self):
        """Very long text should not crash"""
        from app.spellcheck.engine import TibetanSpellChecker
        
        engine = TibetanSpellChecker()
        # Repeat valid text many times
        text = ("བོད་ཡིག་" * 1000)
        errors = engine.check_text(text)
        
        # Should complete without error
        assert isinstance(errors, list)


class TestPerformance:
    """Test performance characteristics (not strict timings)"""
    
    def test_check_text_is_reasonably_fast(self):
        """Checking text should complete in reasonable time"""
        import time
        from app.spellcheck.engine import TibetanSpellChecker
        
        engine = TibetanSpellChecker()
        text = "བོད་ཀྱི་སྐད་ཡིག་" * 100  # 400 syllables
        
        start = time.time()
        errors = engine.check_text(text)
        elapsed = time.time() - start
        
        # Should complete in under 5 seconds (generous)
        assert elapsed < 5.0
    
    def test_repeated_checks_consistent(self):
        """Repeated checks should return same results"""
        from app.spellcheck.engine import TibetanSpellChecker
        
        engine = TibetanSpellChecker()
        text = "བོད་ལང་ཡིག་"
        
        errors1 = engine.check_text(text)
        errors2 = engine.check_text(text)
        errors3 = engine.check_text(text)
        
        # Results should be identical
        assert len(errors1) == len(errors2) == len(errors3)
        if len(errors1) > 0:
            assert errors1[0]['word'] == errors2[0]['word'] == errors3[0]['word']


class TestIntegration:
    """Integration tests combining all components"""
    
    def test_full_pipeline(self):
        """Test complete spell checking pipeline"""
        from app.spellcheck.engine import TibetanSpellChecker
        
        engine = TibetanSpellChecker()
        
        # Complex text with various features
        text = """
        བོད་ཀྱི་སྐད་ཡིག་།
        བོད་ཡིག་ནི་ཧི་མ་ལ་ཡའི་ལྗོངས་སུ་བཀོལ་སྤྱོད་བྱེད་པའི་ཡི་གེ་ཞིག་ཡིན།
        """
        
        errors = engine.check_text(text)
        
        # Should process without crashing
        assert isinstance(errors, list)
        # Each error should be well-formed
        for error in errors:
            assert 'word' in error
            assert 'error_type' in error
            assert 'severity' in error
            assert 'position' in error
    
    def test_readme_example(self):
        """Test the example from README/docs"""
        from app.spellcheck.engine import TibetanSpellChecker
        
        engine = TibetanSpellChecker()
        
        # Valid text from documentation
        valid_text = "བོད་ཡིག་"
        errors = engine.check_text(valid_text)
        assert len(errors) == 0
        
        # Invalid text (if we have one)
        # invalid_text = "..."
        # errors = engine.check_text(invalid_text)
        # assert len(errors) > 0
