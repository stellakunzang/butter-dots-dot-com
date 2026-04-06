"""
Corpus API endpoints — word corpus statistics.
"""
from fastapi import APIRouter

from app.schemas.spellcheck import CorpusStatsResponse
from app.spellcheck.dictionary import DictionaryService

router = APIRouter()

# Shared instance — loaded once at module import time.
_dictionary = DictionaryService()


@router.get("/corpus/stats", response_model=CorpusStatsResponse)
async def corpus_stats():
    """
    Return statistics about the loaded word corpus.

    - **available**: whether dictionary lookup is active (requires DATABASE_URL
      and a populated spelling_reference table)
    - **word_count**: number of entries in spelling_reference
    - **syllable_count**: unique syllables extracted from all entries
    """
    return CorpusStatsResponse(**_dictionary.stats())
