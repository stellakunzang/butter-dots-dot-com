"""Engine-level Sanskrit reclassification (check_text).

The low-level scorer lives in test_sanskrit_detector.py. These tests cover how
the engine *uses* it: errors sitting on likely-Sanskrit syllables are downgraded
to an info-level `foreign_transliteration` note (keeping the original structural
reason), while genuine Tibetan misspellings and critical encoding errors are
left untouched.
"""

from app.spellcheck.engine import TibetanSpellChecker


def _by_type(errors, error_type):
    return [e for e in errors if e.get("error_type") == error_type]


class TestSanskritReclassification:
    def test_mantra_syllables_downgraded_to_info(self):
        """A mantra run reads as Sanskrit, not a wall of spelling errors."""
        checker = TibetanSpellChecker()
        # Medicine Buddha mantra fragment: Sanskrit written in Tibetan script.
        errors = checker.check_text("ཨོཾ་ན་མོ་བྷ་ག་ཝ་ཏེ་བྷེ་ཥ་ཛྱཻ")

        reclassified = _by_type(errors, "foreign_transliteration")
        assert reclassified, "expected mantra syllables to be reclassified"
        for e in reclassified:
            assert e["severity"] == "info"
            assert e["original_error_type"], "original structural reason must be kept"
            assert "Sanskrit" in e["message"]

        # Nothing genuine (non-info) should survive on this pure-mantra line.
        genuine = [e for e in errors if e["severity"] != "info"]
        assert not genuine, f"unexpected genuine errors on a mantra: {genuine}"

    def test_original_reason_is_preserved(self):
        """Downgrading keeps the structural reason so nothing is silently lost."""
        checker = TibetanSpellChecker()
        # ཧཾ (ha + anusvara): a marker-bearing Sanskrit syllable that is NOT on
        # the common-Sanskrit allowlist, so it flows through the heuristic
        # reclassification rather than being silently valid.
        errors = checker.check_text("ཧཾ")

        notes = _by_type(errors, "foreign_transliteration")
        assert len(notes) == 1
        assert notes[0]["original_error_type"] == "unparsed_characters"
        assert notes[0]["word"] == "ཧཾ"

    def test_real_misspelling_stays_a_hard_error(self):
        """A genuine Tibetan misspelling must not be hidden as Sanskrit."""
        checker = TibetanSpellChecker()
        errors = checker.check_text("བོད་གཀར་")  # གཀར: ga cannot prefix ka

        assert not _by_type(errors, "foreign_transliteration")
        hard = [e for e in errors if e["severity"] == "error"]
        assert any(e["word"] == "གཀར" for e in hard)

    def test_clean_tibetan_unaffected(self):
        checker = TibetanSpellChecker()
        errors = checker.check_text("བཀྲ་ཤིས་བདེ་ལེགས།")
        assert not _by_type(errors, "foreign_transliteration")

    def test_critical_encoding_error_is_protected(self):
        """Corruption (encoding_error/wrong_unicode) is never softened to info.

        A broken-byte error means the text is damaged, not that the author chose
        Sanskrit — so even on a Sanskrit-looking syllable it stays critical. A
        co-located non-critical error on the same syllable still downgrades.
        """
        checker = TibetanSpellChecker()
        text = "ཨོཾ"  # anusvara → scores as Sanskrit
        errors = [
            {"word": "ཨོཾ", "position": 0, "error_type": "encoding_error", "severity": "critical"},
            {"word": "ཨོཾ", "position": 0, "error_type": "invalid_subscript", "severity": "error"},
        ]
        checker._reclassify_sanskrit_errors(text, errors)

        assert errors[0]["error_type"] == "encoding_error"
        assert errors[0]["severity"] == "critical"
        assert errors[1]["error_type"] == "foreign_transliteration"
        assert errors[1]["severity"] == "info"
        assert errors[1]["original_error_type"] == "invalid_subscript"
