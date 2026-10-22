"""
Corpus API endpoints — word corpus statistics.
"""

from fastapi import APIRouter

from app.schemas.spellcheck import CorpusStatsResponse
from app.spellcheck.dictionary import DictionaryService

router = APIRouter()

_dictionary: DictionaryService | None = None


def get_dictionary() -> DictionaryService:
    """Return the shared corpus, creating it on first use."""
    global _dictionary
    if _dictionary is None:
        _dictionary = DictionaryService()
    return _dictionary


@router.get("/corpus/stats", response_model=CorpusStatsResponse)
async def corpus_stats():
    """
    Return statistics about the loaded word corpus.

    - **available**: whether dictionary lookup is active (requires DATABASE_URL
      and a populated word table)
    - **word_count**: number of entries in word
    - **syllable_count**: unique syllables extracted from all entries
    """
    return CorpusStatsResponse(**get_dictionary().stats())
