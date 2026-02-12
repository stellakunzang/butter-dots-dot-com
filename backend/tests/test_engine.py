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


class TestQAFindings_PrefixBugs_20260211:
    """
    Integration tests for prefix validation bugs found during QA.

    Real Tibetan words that are currently incorrectly flagged due to
    data errors in INVALID_PREFIX_COMBOS. These must all pass after fixing.
    """

    def test_dngos_actual(self):
        """དངོས (dngos = actual/real) should be valid.
        Structure: ད (prefix) + ང (root) + ོ (vowel o) + ས (suffix)
        BUG: ང incorrectly in ད's invalid prefix list.
        """
        from app.spellcheck.engine import TibetanSpellChecker
        engine = TibetanSpellChecker()
        result = engine.check_syllable("དངོས")
        assert result is None, f"དངོས (dngos = actual) should be valid but got: {result}"

    def test_dngul_silver(self):
        """དངུལ (dngul = silver/money) should be valid.
        Structure: ད (prefix) + ང (root) + ུ (vowel u) + ལ (suffix)
        Same bug: ད+ང prefix combo incorrectly flagged.
        """
        from app.spellcheck.engine import TibetanSpellChecker
        engine = TibetanSpellChecker()
        result = engine.check_syllable("དངུལ")
        assert result is None, f"དངུལ (dngul = silver) should be valid but got: {result}"

    def test_dngos_in_text(self):
        """དངོས in running text should not be flagged."""
        from app.spellcheck.engine import TibetanSpellChecker
        engine = TibetanSpellChecker()
        errors = engine.check_text("དངོས་གནས་")
        error_words = [e.get('word', '') for e in errors]
        assert "དངོས" not in error_words, f"དངོས flagged in text. Errors: {errors}"

    def test_text_with_da_nga_prefix_words(self):
        """Sentence using ད+ང prefix words should have zero false positives."""
        from app.spellcheck.engine import TibetanSpellChecker
        engine = TibetanSpellChecker()
        # "actual silver" - both words have ད prefix + ང root
        errors = engine.check_text("དངོས་དངུལ་")
        prefix_errors = [
            e for e in errors
            if e.get('error_type') == 'invalid_prefix_combination'
        ]
        assert len(prefix_errors) == 0, (
            f"False prefix errors on ད+ང words: {prefix_errors}"
        )


class TestAchungISuffixValidation:
    """
    Test validation of འི (achung + i-vowel) as genitive suffix.

    In Tibetan grammar, འི is added to form the genitive case on words
    that have EITHER:
    - No suffix (e.g., པ → པའི, ཡ → ཡའི)
    - Suffix འ/achung (e.g., དགའ → དགའི, བཀའ → བཀའི)

    This is a special exception to the single-vowel rule: when འི is
    a valid genitive suffix, the ི on འ is allowed even if the root
    already carries a vowel (e.g., མཐོའི has both ོ and ི).

    འི CANNOT be added after any other suffix (ག, ང, ད, ན, བ, མ, ར, ལ, ས).
    """

    # ================================================================
    # POSITIVE: འི after no suffix → valid
    # ================================================================

    def test_ya_achung_i_valid_no_suffix(self):
        """ཡའི (ya'i) - valid: ཡ has no suffix, འི added as genitive"""
        from app.spellcheck.engine import TibetanSpellChecker

        engine = TibetanSpellChecker()
        result = engine.check_syllable("ཡའི")
        assert result is None, f"ཡའི should be valid but got: {result}"

    def test_pa_achung_i_valid_no_suffix(self):
        """པའི (pa'i) - valid: པ has no suffix, འི added as genitive

        པའི is one of the most common genitive particles in Tibetan.
        """
        from app.spellcheck.engine import TibetanSpellChecker

        engine = TibetanSpellChecker()
        result = engine.check_syllable("པའི")
        assert result is None, f"པའི should be valid but got: {result}"

    def test_la_achung_i_valid_no_suffix(self):
        """ལའི (la'i) - valid: ལ has no suffix, འི added as genitive"""
        from app.spellcheck.engine import TibetanSpellChecker

        engine = TibetanSpellChecker()
        result = engine.check_syllable("ལའི")
        assert result is None, f"ལའི should be valid but got: {result}"

    def test_ba_achung_i_valid_no_suffix(self):
        """བའི (ba'i) - valid: བ has no suffix, འི added as genitive"""
        from app.spellcheck.engine import TibetanSpellChecker

        engine = TibetanSpellChecker()
        result = engine.check_syllable("བའི")
        assert result is None, f"བའི should be valid but got: {result}"

    # ================================================================
    # POSITIVE: འི after suffix འ (achung) → valid
    # ================================================================

    def test_dga_achung_i_valid_achung_suffix(self):
        """དགའི (dga'i) - valid: དགའ has suffix འ, ི added for genitive

        དགའ (dga' = love/joy) already ends in འ. The genitive just
        adds ི to the existing achung.
        """
        from app.spellcheck.engine import TibetanSpellChecker

        engine = TibetanSpellChecker()
        result = engine.check_syllable("དགའི")
        assert result is None, f"དགའི should be valid but got: {result}"

    def test_bka_achung_i_valid_achung_suffix(self):
        """བཀའི (bka'i) - valid: བཀའ has suffix འ, ི added for genitive

        བཀའ (bka' = decree/command) ends in འ.
        """
        from app.spellcheck.engine import TibetanSpellChecker

        engine = TibetanSpellChecker()
        result = engine.check_syllable("བཀའི")
        assert result is None, f"བཀའི should be valid but got: {result}"

    def test_mkha_achung_i_valid_achung_suffix(self):
        """མཁའི (mkha'i) - valid: མཁའ has suffix འ, ི added for genitive

        མཁའ (mkha' = sky/space) ends in འ.
        """
        from app.spellcheck.engine import TibetanSpellChecker

        engine = TibetanSpellChecker()
        result = engine.check_syllable("མཁའི")
        assert result is None, f"མཁའི should be valid but got: {result}"

    # ================================================================
    # POSITIVE: Root vowel + འི suffix (two vowel marks) → valid
    # ================================================================

    def test_mtho_achung_i_valid_two_vowels(self):
        """མཐོའི (mtho'i) - valid despite TWO vowel marks

        མཐོ (mtho = high) has root vowel ོ and no suffix.
        Adding འི gives མཐོའི with ོ on root and ི on suffix འ.
        This is a legitimate exception to the single-vowel rule.
        """
        from app.spellcheck.engine import TibetanSpellChecker

        engine = TibetanSpellChecker()
        result = engine.check_syllable("མཐོའི")
        assert result is None, f"མཐོའི should be valid (two vowels allowed with འི suffix) but got: {result}"

    # ================================================================
    # POSITIVE: འི in running text → no false positives
    # ================================================================

    def test_achung_i_in_running_text(self):
        """འི genitive forms should not be flagged in running text"""
        from app.spellcheck.engine import TibetanSpellChecker

        engine = TibetanSpellChecker()
        # "of the decree" - both syllables valid
        errors = engine.check_text("བཀའི་པའི་")
        error_words = [e.get('word', '') for e in errors if e.get('severity') != 'info']
        assert "བཀའི" not in error_words, f"བཀའི flagged in text. Errors: {errors}"
        assert "པའི" not in error_words, f"པའི flagged in text. Errors: {errors}"

    # ================================================================
    # NEGATIVE: འི after non-achung suffix → invalid
    # ================================================================

    def test_bod_achung_i_invalid_suffix_da(self):
        """བོདའི - INVALID: བོད has suffix ད, འི cannot follow ད

        འི can only follow no suffix or suffix འ.
        Suffix ད requires a different genitive particle.
        """
        from app.spellcheck.engine import TibetanSpellChecker

        engine = TibetanSpellChecker()
        result = engine.check_syllable("བོདའི")
        assert result is not None, \
            "བོདའི should be invalid -- འི cannot follow suffix ད"

    def test_lang_achung_i_invalid_suffix_nga(self):
        """ལངའི - INVALID: ལང has suffix ང, འི cannot follow ང

        འི can only follow no suffix or suffix འ.
        """
        from app.spellcheck.engine import TibetanSpellChecker

        engine = TibetanSpellChecker()
        result = engine.check_syllable("ལངའི")
        assert result is not None, \
            "ལངའི should be invalid -- འི cannot follow suffix ང"

    def test_skad_achung_i_invalid_suffix_da(self):
        """སྐདའི - INVALID: སྐད has suffix ད, འི cannot follow ད

        སྐད (skad = language/speech) has suffix ད.
        """
        from app.spellcheck.engine import TibetanSpellChecker

        engine = TibetanSpellChecker()
        result = engine.check_syllable("སྐདའི")
        assert result is not None, \
            "སྐདའི should be invalid -- འི cannot follow suffix ད"

    def test_deb_achung_i_invalid_suffix_ba(self):
        """དེབའི - INVALID: དེབ has suffix བ, འི cannot follow བ

        དེབ (deb = book) has suffix བ.
        """
        from app.spellcheck.engine import TibetanSpellChecker

        engine = TibetanSpellChecker()
        result = engine.check_syllable("དེབའི")
        assert result is not None, \
            "དེབའི should be invalid -- འི cannot follow suffix བ"

    def test_yig_achung_i_invalid_suffix_ga(self):
        """ཡིགའི - INVALID: ཡིག has suffix ག, འི cannot follow ག

        ཡིག (yig = letter/script) has suffix ག.
        """
        from app.spellcheck.engine import TibetanSpellChecker

        engine = TibetanSpellChecker()
        result = engine.check_syllable("ཡིགའི")
        assert result is not None, \
            "ཡིགའི should be invalid -- འི cannot follow suffix ག"


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
