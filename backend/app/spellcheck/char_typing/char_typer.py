"""
Tibetan Character Typer

Classifies each character in a string by its Unicode type.
This is purely Unicode-based -- no syllable role assignment happens here.

Usage:
    typed = type_characters("སྐད")
    # [TypedChar('ས', BASE, 0, 'ས'), TypedChar('ྐ', SUBJOINED, 1, 'ཀ'), TypedChar('ད', BASE, 2, 'ད')]
"""
from typing import List
from ..data_types import TypedChar, CharType


# Unicode ranges for Tibetan characters
_BASE_START = 0x0F40
_BASE_END = 0x0F6C
_SUBJOINED_START = 0x0F90
_SUBJOINED_END = 0x0FBC
_VOWEL_START = 0x0F71
_VOWEL_END = 0x0F7C
_TIBETAN_START = 0x0F00
_TIBETAN_END = 0x0FFF
_SUBJOINED_OFFSET = 0x50  # Subjoined = Base + 0x50


def type_characters(text: str) -> List[TypedChar]:
    """
    Classify each character in a Tibetan string by its Unicode type.

    Each character gets a CharType (BASE, SUBJOINED, VOWEL, MARK, OTHER)
    and its base_form (subjoined consonants converted to base form).

    Args:
        text: A Tibetan syllable string (no tsheg)

    Returns:
        List of TypedChar, one per character
    """
    result = []
    for i, char in enumerate(text):
        code = ord(char)

        if _BASE_START <= code <= _BASE_END:
            result.append(TypedChar(
                char=char,
                type=CharType.BASE,
                position=i,
                base_form=char,
            ))

        elif _SUBJOINED_START <= code <= _SUBJOINED_END:
            result.append(TypedChar(
                char=char,
                type=CharType.SUBJOINED,
                position=i,
                base_form=chr(code - _SUBJOINED_OFFSET),
            ))

        elif _VOWEL_START <= code <= _VOWEL_END:
            result.append(TypedChar(
                char=char,
                type=CharType.VOWEL,
                position=i,
                base_form=char,
            ))

        elif _TIBETAN_START <= code <= _TIBETAN_END:
            result.append(TypedChar(
                char=char,
                type=CharType.MARK,
                position=i,
                base_form=char,
            ))

        else:
            result.append(TypedChar(
                char=char,
                type=CharType.OTHER,
                position=i,
                base_form=char,
            ))

    return result
