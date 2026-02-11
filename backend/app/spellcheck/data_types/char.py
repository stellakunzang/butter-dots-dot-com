"""
Character-level data types for the spellcheck pipeline.
"""
from dataclasses import dataclass
from enum import Enum


class CharType(Enum):
    """Unicode-based character classification for Tibetan characters."""
    BASE = "base"              # Base consonant (U+0F40-0F6C)
    SUBJOINED = "subjoined"    # Subjoined consonant (U+0F90-0FBC)
    VOWEL = "vowel"            # Vowel mark (U+0F71-0F7C)
    MARK = "mark"              # Other Tibetan marks (U+0F00-0F3F, etc.)
    OTHER = "other"            # Non-Tibetan or unrecognized


@dataclass
class TypedChar:
    """
    A Tibetan character paired with its Unicode-based type.

    This is the output of character classification (char_typer.py).
    No syllable role (superscript, root, etc.) is assigned at this stage --
    that is the parser's job.

    Attributes:
        char: The original character
        type: Unicode-based classification (BASE, SUBJOINED, VOWEL, etc.)
        position: Index in the original string
        base_form: Base consonant form (subjoined converted to base, others unchanged)
    """
    char: str
    type: CharType
    position: int
    base_form: str
