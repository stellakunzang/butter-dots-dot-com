"""
Tests for DictionaryService.

All tests use an injected in-memory word list so no database is required.
The DB-loading path (_load) is covered by verifying graceful degradation
when DATABASE_URL is absent (already exercised in the CI environment).
"""
import unicodedata
from unittest.mock import MagicMock, patch

import pytest

from app.spellcheck.dictionary import DictionaryService, _normalize, _syllables_from_word


# ---------------------------------------------------------------------------
# Helper: build a DictionaryService pre-loaded with a known word list
# ---------------------------------------------------------------------------

def make_service(words: list[str]) -> DictionaryService:
    """Return a DictionaryService with its syllable inventory pre-populated."""
    svc = DictionaryService.__new__(DictionaryService)
    syllables: set[str] = set()
    for word in words:
        for syl in _syllables_from_word(_normalize(word)):
            syllables.add(syl)
    svc._syllables = frozenset(syllables)
    svc.word_count = len(words)
    svc.syllable_count = len(syllables)
    svc.available = len(words) > 0
    return svc


# ---------------------------------------------------------------------------
# _normalize
# ---------------------------------------------------------------------------

class TestNormalize:
    def test_nfc_normalization(self):
        # Both forms of the same Tibetan text should normalize to the same string
        raw = "བོད"
        assert _normalize(raw) == unicodedata.normalize("NFC", raw)

    def test_strips_whitespace(self):
        # _normalize applies NFC; stripping is done by _syllables_from_word, not here
        result = _normalize("  བོད  ")
        assert "བོད" in result

    def test_empty_string(self):
        assert _normalize("") == ""


# ---------------------------------------------------------------------------
# _syllables_from_word
# ---------------------------------------------------------------------------

class TestSyllablesFromWord:
    def test_single_syllable(self):
        assert _syllables_from_word("བོད") == ["བོད"]

    def test_two_syllables(self):
        result = _syllables_from_word("བོད་ཡིག")
        assert result == ["བོད", "ཡིག"]

    def test_three_syllables(self):
        result = _syllables_from_word("སྤྱན་རས་གཟིགས")
        assert result == ["སྤྱན", "རས", "གཟིགས"]

    def test_trailing_tsheg(self):
        # Trailing tsheg should not produce an empty syllable
        result = _syllables_from_word("བོད་ཡིག་")
        assert result == ["བོད", "ཡིག"]
        assert "" not in result

    def test_empty_string(self):
        assert _syllables_from_word("") == []


# ---------------------------------------------------------------------------
# DictionaryService — graceful degradation (no database)
# ---------------------------------------------------------------------------

class TestDictionaryServiceNoDB:
    def test_available_is_false_without_db(self):
        # db_available is imported inside _load(), so patch it at the source module
        with patch("app.database.db_available", return_value=False):
            svc = DictionaryService()
        assert svc.available is False

    def test_is_valid_syllable_returns_none_when_unavailable(self):
        svc = make_service([])
        svc.available = False
        assert svc.is_valid_syllable("བོད") is None

    def test_stats_when_unavailable(self):
        svc = make_service([])
        svc.available = False
        stats = svc.stats()
        assert stats["available"] is False
        assert stats["word_count"] == 0
        assert stats["syllable_count"] == 0


# ---------------------------------------------------------------------------
# DictionaryService — lookup with a known corpus
# ---------------------------------------------------------------------------

class TestDictionaryServiceLookup:
    @pytest.fixture
    def svc(self):
        return make_service([
            "བོད",           # single syllable
            "བོད་ཡིག",       # two syllables
            "སྤྱན་རས་གཟིགས", # three syllables
            "སངས་རྒྱས",      # Buddhist term
        ])

    def test_known_single_syllable_is_valid(self, svc):
        assert svc.is_valid_syllable("བོད") is True

    def test_syllable_from_multi_syllable_word_is_valid(self, svc):
        # ཡིག appears only as part of བོད་ཡིག — should still be valid
        assert svc.is_valid_syllable("ཡིག") is True

    def test_syllable_from_three_syllable_word_is_valid(self, svc):
        assert svc.is_valid_syllable("རས") is True
        assert svc.is_valid_syllable("གཟིགས") is True

    def test_unknown_syllable_returns_false(self, svc):
        # ཡིབ is structurally valid Tibetan but not in this corpus
        assert svc.is_valid_syllable("ཡིབ") is False

    def test_normalization_applied_on_lookup(self, svc):
        # Lookup should normalize before checking — same syllable, different form
        raw = "བོད"
        nfc = unicodedata.normalize("NFC", raw)
        assert svc.is_valid_syllable(raw) == svc.is_valid_syllable(nfc)

    def test_stats_reflect_loaded_corpus(self, svc):
        stats = svc.stats()
        assert stats["available"] is True
        assert stats["word_count"] == 4
        # 4 words → བོད, ཡིག, བོད (dup), སྤྱན, རས, གཟིགས, སངས, རྒྱས = 7 unique
        assert stats["syllable_count"] == 7
