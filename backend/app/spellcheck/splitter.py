"""
Tibetan Syllable Splitting Utilities

Functions to split Tibetan text into individual syllables.
Promoted from syllable_parser_helpers/syllable_splitter.py.
"""
from typing import List, Dict

from .normalizer import is_tibetan_punctuation_char

# Tibetan punctuation marks used as explicit constants (also covered by
# is_tibetan_punctuation_char, listed here for readability at call sites).
TSHEG = '\u0F0B'  # ་ syllable separator
SHAD = '\u0F0D'   # ། sentence ending
DOUBLE_SHAD = '\u0F0E'  # ༎ topic ending
SPACE = '\u0F0C'  # ༌ non-breaking space

_ASCII_WHITESPACE = frozenset({' ', '\t', '\n', '\r'})


def is_syllable_delimiter(char: str) -> bool:
    """
    Return True if ``char`` should end the current syllable.

    Delimiters: tsheg, ASCII whitespace, and Tibetan punctuation/marks
    (shad variants, gter tsheg, sbrul shad, yig mgo, rnam bcad, etc.).
    """
    if not char:
        return False
    if char in _ASCII_WHITESPACE:
        return True
    return is_tibetan_punctuation_char(char)


def split_syllables(text: str) -> List[str]:
    """
    Split Tibetan text into syllables by tsheg and other punctuation.

    Args:
        text: Tibetan text string

    Returns:
        List of syllable strings (without tsheg or punctuation)

    Example:
        "བོད་ཡིག" → ["བོད", "ཡིག"]
        "བོད༔ཡིག" → ["བོད", "ཡིག"]
    """
    syllables = []
    current = []

    for char in text:
        if is_syllable_delimiter(char):
            if current:
                syllables.append(''.join(current).strip())
                current = []
        else:
            current.append(char)

    if current:
        syllables.append(''.join(current).strip())

    return [s for s in syllables if s]


def split_syllables_with_position(text: str) -> List[Dict[str, any]]:
    """
    Split Tibetan text into syllables with character position tracking.

    Useful for spell checking - positions allow highlighting errors in original text.

    Args:
        text: Tibetan text string

    Returns:
        List of dicts with 'syllable' and 'position' keys

    Example:
        "བོད་ཡིག" → [
            {'syllable': 'བོད', 'position': 0},
            {'syllable': 'ཡིག', 'position': 5}
        ]
        "ལསཿསྨན" → [
            {'syllable': 'ལས', 'position': 0},
            {'syllable': 'སྨན', 'position': 3}
        ]
    """
    result = []
    current_pos = 0
    current_syllable = ""

    for i, char in enumerate(text):
        if is_syllable_delimiter(char):
            if current_syllable:
                result.append({
                    'syllable': current_syllable,
                    'position': current_pos
                })
                current_syllable = ""
                current_pos = i + 1
            else:
                # Skip leading/consecutive delimiters; next syllable starts after.
                current_pos = i + 1
        else:
            if not current_syllable:
                current_pos = i
            current_syllable += char

    if current_syllable:
        result.append({
            'syllable': current_syllable,
            'position': current_pos
        })

    return result
