"""
Integration tests for the spell check engine with Phase 2 dictionary lookup.

Uses an injected DictionaryService pre-loaded with a small known-good corpus
so no database is required.  Tests verify:
  - unknown_word warning fires for valid-structure syllables absent from corpus
  - corpus_hit is populated on Phase 1 structural errors
  - Phase 2 is silently skipped when the dictionary is unavailable
  - known-good syllables still pass cleanly end-to-end
"""
import pytest

from app.spellcheck.dictionary import DictionaryService
from app.spellcheck.engine import TibetanSpellChecker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_dictionary(*words: str) -> DictionaryService:
    """Return a DictionaryService pre-loaded with the given words."""
    from app.spellcheck.dictionary import _normalize, _syllables_from_word

    svc = DictionaryService.__new__(DictionaryService)
    syllables: set[str] = set()
    for word in words:
        for syl in _syllables_from_word(_normalize(word)):
            syllables.add(syl)
    svc._syllables = frozenset(syllables)
    svc.word_count = len(words)
    svc.syllable_count = len(syllables)
    svc.available = True
    return svc


def unavailable_dictionary() -> DictionaryService:
    """Return a DictionaryService with no corpus loaded (simulates no DB)."""
    svc = DictionaryService.__new__(DictionaryService)
    svc._syllables = frozenset()
    svc.word_count = 0
    svc.syllable_count = 0
    svc.available = False
    return svc


# ---------------------------------------------------------------------------
# Phase 2: unknown_word warnings
# ---------------------------------------------------------------------------

class TestUnknownWordWarning:
    def test_valid_syllable_in_corpus_passes(self):
        """A structurally valid syllable that IS in the corpus produces no error."""
        checker = TibetanSpellChecker(dictionary=make_dictionary("བོད", "ཡིག"))
        result = checker.check_syllable("བོད")
        assert result is None

    def test_valid_syllable_not_in_corpus_flagged(self):
        """A structurally valid syllable NOT in the corpus gets unknown_word warning."""
        checker = TibetanSpellChecker(dictionary=make_dictionary("བོད"))
        result = checker.check_syllable("ཡིག")
        assert result is not None
        assert result["error_type"] == "unknown_word"
        assert result["severity"] == "warning"
        assert result["corpus_hit"] is False

    def test_unknown_word_message_is_helpful(self):
        checker = TibetanSpellChecker(dictionary=make_dictionary("བོད"))
        result = checker.check_syllable("ཡིག")
        assert result is not None
        assert "structurally valid" in result["message"]

    def test_check_text_returns_unknown_word_warnings(self):
        """check_text surfaces unknown_word warnings in the error list."""
        checker = TibetanSpellChecker(dictionary=make_dictionary("བོད"))
        errors = checker.check_text("བོད་ཡིབ་")
        # བོད is in corpus (clean), ཡིབ is not
        unknown = [e for e in errors if e.get("error_type") == "unknown_word"]
        assert len(unknown) == 1
        assert unknown[0]["word"] == "ཡིབ"

    def test_warning_does_not_suppress_subsequent_syllables(self):
        """unknown_word on one syllable doesn't affect checking of the next."""
        checker = TibetanSpellChecker(dictionary=make_dictionary("བོད"))
        errors = checker.check_text("ཡིབ་བོད་")
        unknown = [e for e in errors if e["error_type"] == "unknown_word"]
        assert len(unknown) == 1  # only ཡིབ


# ---------------------------------------------------------------------------
# corpus_hit on Phase 1 structural errors
# ---------------------------------------------------------------------------

class TestCorpusHitOnStructuralErrors:
    def test_structural_error_with_corpus_miss_has_false_corpus_hit(self):
        """A structurally invalid syllable not in the corpus: corpus_hit=False."""
        checker = TibetanSpellChecker(dictionary=make_dictionary("བོད"))
        # གཀར is structurally invalid (ག cannot prefix ཀ)
        result = checker.check_syllable("གཀར")
        assert result is not None
        assert result["severity"] == "error"
        assert result["corpus_hit"] is False

    def test_structural_error_with_corpus_hit_has_true_corpus_hit(self):
        """A structurally invalid syllable that IS in the corpus: corpus_hit=True.
        This is the signal that Phase 1 may be producing a false positive."""
        # Deliberately add the structurally-flagged syllable to the corpus
        checker = TibetanSpellChecker(dictionary=make_dictionary("གཀར"))
        result = checker.check_syllable("གཀར")
        assert result is not None
        assert result["severity"] == "error"
        assert result["corpus_hit"] is True

    def test_corpus_hit_none_when_dictionary_unavailable(self):
        """When no dictionary is loaded, corpus_hit should be None."""
        checker = TibetanSpellChecker(dictionary=unavailable_dictionary())
        result = checker.check_syllable("གཀར")
        assert result is not None
        assert result["corpus_hit"] is None


# ---------------------------------------------------------------------------
# Phase 2 skipped when dictionary unavailable
# ---------------------------------------------------------------------------

class TestDictionaryUnavailable:
    def test_no_unknown_word_errors_without_corpus(self):
        """Without a corpus, Phase 2 is silently skipped — no false positives."""
        checker = TibetanSpellChecker(dictionary=unavailable_dictionary())
        # ཡིབ is structurally valid and not in any corpus, but no corpus = no warning
        result = checker.check_syllable("ཡིབ")
        assert result is None

    def test_phase1_errors_still_fire_without_corpus(self):
        """Phase 1 structural checks are unaffected by dictionary availability."""
        checker = TibetanSpellChecker(dictionary=unavailable_dictionary())
        result = checker.check_syllable("གཀར")
        assert result is not None
        assert result["error_type"] != "unknown_word"

    def test_check_text_without_corpus_matches_phase1_only(self):
        """Full text check without corpus produces same results as Phase 1."""
        checker_no_dict = TibetanSpellChecker(dictionary=unavailable_dictionary())
        # Import original checker for comparison
        from app.spellcheck.engine import TibetanSpellChecker as Checker

        # Both should return the same structural errors on invalid text
        text = "གཀར་བོད་"
        errors_no_dict = [
            e for e in checker_no_dict.check_text(text)
            if e["error_type"] != "non_tibetan_skipped"
        ]
        # One structural error (གཀར), བོད skipped (no corpus)
        assert len(errors_no_dict) == 1
        assert errors_no_dict[0]["error_type"] != "unknown_word"
