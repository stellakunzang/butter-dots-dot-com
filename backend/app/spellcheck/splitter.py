"""
Tibetan Syllable Splitting Utilities

Functions to split Tibetan text into individual syllables.
Promoted from syllable_parser_helpers/syllable_splitter.py.
"""
from typing import List, Dict

# Tibetan punctuation marks
TSHEG = '\u0F0B'  # ་ syllable separator
SHAD = '\u0F0D'   # ། sentence ending
DOUBLE_SHAD = '\u0F0E'  # ༎ topic ending
SPACE = '\u0F0C'  # ༌ non-breaking space


def split_syllables(text: str) -> List[str]:
    """
    Split Tibetan text into syllables by tsheg (་).

    Args:
        text: Tibetan text string

    Returns:
        List of syllable strings (without tsheg or punctuation)

    Example:
        "བོད་ཡིག" → ["བོད", "ཡིག"]
    """
    text = text.replace(SHAD, TSHEG)
    text = text.replace(DOUBLE_SHAD, TSHEG)
    text = text.replace(SPACE, TSHEG)

    syllables = text.split(TSHEG)
    syllables = [s.strip() for s in syllables if s.strip()]

    return syllables


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
    """
    result = []
    current_pos = 0
    current_syllable = ""

    for i, char in enumerate(text):
        if char in [TSHEG, SHAD, DOUBLE_SHAD, SPACE, ' ', '\t', '\n']:
            if current_syllable:
                result.append({
                    'syllable': current_syllable,
                    'position': current_pos
                })
                current_syllable = ""
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
