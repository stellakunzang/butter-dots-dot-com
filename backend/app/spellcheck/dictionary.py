"""
DictionaryService — Phase 2 word corpus lookup.

Loads all entries from the word table at construction time,
extracts every individual syllable from every word (splitting on tsheg), and
builds an in-memory frozenset for O(1) per-syllable validity checks.

This sidesteps the Tibetan word-segmentation problem: rather than trying to
identify word boundaries in the input text (which requires a probabilistic
model), we ask a simpler question: "does this syllable appear in any legitimate
Tibetan word in our corpus?"  A syllable like ཡིབ that is structurally valid
but never occurs in real Tibetan will not be in the inventory and gets flagged.

Limitation: cannot detect valid-syllable sequences that form nonsense compounds
(e.g. བོད་ཡིབ་).  That requires word segmentation and is deferred to Phase 3.

Usage:
    from app.spellcheck.dictionary import DictionaryService

    svc = DictionaryService()          # loads from DB, or no-op if unavailable
    if svc.available:
        valid = svc.is_valid_syllable("བོད")   # True
        valid = svc.is_valid_syllable("ཡིབ")   # False
    else:
        # No database — Phase 1 only, no dictionary check
        pass
"""
import logging
import unicodedata
from typing import Optional

logger = logging.getLogger(__name__)

TSHEG = "\u0F0B"  # ་


def _normalize(text: str) -> str:
    """NFC-normalize Tibetan text (consistent with the spellcheck normalizer)."""
    return unicodedata.normalize("NFC", text)


def _syllables_from_word(word: str) -> list[str]:
    """
    Split a dictionary entry (possibly multi-syllable) into its component
    syllables.  Strips leading/trailing whitespace from each piece.
    """
    return [s.strip() for s in word.split(TSHEG) if s.strip()]


class DictionaryService:
    """
    In-memory syllable inventory built from the word table.

    Attributes:
        available: True if a database was reachable and at least one word
                   was loaded.  When False, is_valid_syllable returns None
                   and callers should skip the dictionary check entirely.
        word_count: Number of corpus entries loaded.
        syllable_count: Number of unique syllables in the inventory.
    """

    def __init__(self) -> None:
        self._syllables: frozenset[str] = frozenset()
        self.word_count: int = 0
        self.syllable_count: int = 0
        self.available: bool = False
        self._load()

    def _load(self) -> None:
        """Query word and build the syllable inventory."""
        try:
            from app.database import db_available, get_session
        except ImportError:
            logger.debug("database module not available; dictionary disabled")
            return

        if not db_available():
            logger.info(
                "No database connection; dictionary lookup disabled (Phase 1 only)"
            )
            return

        try:
            from sqlalchemy import text

            with get_session() as session:
                rows = session.execute(
                    text("SELECT word_normalized FROM word")
                ).fetchall()

            syllable_set: set[str] = set()
            for (word,) in rows:
                for syl in _syllables_from_word(_normalize(word)):
                    syllable_set.add(syl)

            self._syllables = frozenset(syllable_set)
            self.word_count = len(rows)
            self.syllable_count = len(self._syllables)
            self.available = self.word_count > 0

            logger.info(
                "DictionaryService loaded: %d words → %d unique syllables",
                self.word_count,
                self.syllable_count,
            )

        except Exception:
            logger.exception(
                "Failed to load word corpus; dictionary lookup disabled"
            )

    def is_valid_syllable(self, syllable: str) -> Optional[bool]:
        """
        Check whether a syllable appears in the corpus inventory.

        Returns:
            True  — syllable is in the corpus (valid)
            False — syllable is NOT in the corpus (flag as unknown_word)
            None  — corpus not loaded; caller should skip the check
        """
        if not self.available:
            return None
        return _normalize(syllable) in self._syllables

    def stats(self) -> dict:
        """Summary stats for the /corpus/stats API endpoint."""
        return {
            "available": self.available,
            "word_count": self.word_count,
            "syllable_count": self.syllable_count,
        }
