"""
Tibetan Character Type Detection Utilities

Helper functions to identify different types of Tibetan Unicode characters.
"""

# Tibetan Unicode Ranges
BASE_CONSONANT_START = 0x0F40
BASE_CONSONANT_END = 0x0F6C
SUBJOINED_CONSONANT_START = 0x0F90
SUBJOINED_CONSONANT_END = 0x0FBC
VOWEL_START = 0x0F71
VOWEL_END = 0x0F7C

# Import validation sets from rules
from app.spellcheck.rules import (
    VALID_PREFIXES,
    VALID_SUPERSCRIPTS,
    VALID_POST_SUFFIXES
)


def is_base_consonant(char: str) -> bool:
    """Check if character is a base consonant (U+0F40-0F6C)"""
    if not char:
        return False
    return BASE_CONSONANT_START <= ord(char) <= BASE_CONSONANT_END


def is_subjoined_consonant(char: str) -> bool:
    """Check if character is a subjoined consonant (U+0F90-0FBC)"""
    if not char:
        return False
    return SUBJOINED_CONSONANT_START <= ord(char) <= SUBJOINED_CONSONANT_END


def is_vowel(char: str) -> bool:
    """Check if character is a vowel mark (U+0F71-0F7C)"""
    if not char:
        return False
    return VOWEL_START <= ord(char) <= VOWEL_END


def is_prefix(char: str) -> bool:
    """
    Check if character is a valid prefix.
    
    The 6 valid prefixes: ག, ད, བ, མ, འ, ར
    """
    return char in VALID_PREFIXES


def is_superscript(char: str) -> bool:
    """
    Check if character is a valid superscript.
    
    The 3 valid superscripts: ར (ra-mgo), ལ (la-mgo), ས (sa-mgo)
    """
    return char in VALID_SUPERSCRIPTS


def is_post_suffix(char: str) -> bool:
    """
    Check if character is a valid post-suffix.
    
    The 2 valid post-suffixes: ད (da), ས (sa)
    """
    return char in VALID_POST_SUFFIXES
