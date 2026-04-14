"""
Tibetan Unicode Normalization and Character Validation

Handles Unicode normalization (NFC), zero-width character removal,
and Tibetan character validation.
"""
import unicodedata
from typing import Optional, List, Dict


ZERO_WIDTH_CHARS = {'\u200b', '\u200c', '\u200d'}


def normalize_tibetan(text: str) -> str:
    """Normalize to NFC and strip zero-width characters."""
    text = unicodedata.normalize('NFC', text)
    text = text.replace('\u200b', '')  # Zero-width space
    text = text.replace('\u200c', '')  # Zero-width non-joiner
    text = text.replace('\u200d', '')  # Zero-width joiner
    
    return text


def normalize_tibetan_with_position_map(text: str) -> tuple[str, list[int]]:
    """
    Normalize Tibetan text and return a mapping from positions in the
    normalized string back to positions in the original string.

    This allows callers to translate character offsets computed on the
    normalized text into offsets that are correct for the original,
    un-normalized input.

    Args:
        text: Tibetan text to normalize

    Returns:
        (normalized_text, position_map) where ``position_map[i]`` is the
        index in the *original* ``text`` that corresponds to index ``i``
        in ``normalized_text``.
    """
    if not text:
        return ("", [])

    # --- Phase 1: NFC normalization with position tracking ---------------
    nfc_text = unicodedata.normalize('NFC', text)

    # Fast path: NFC is a no-op for the vast majority of Tibetan input.
    if nfc_text == text:
        nfc_to_orig: list[int] = list(range(len(text)))
    else:
        # Build the mapping via incremental prefix normalization.
        # For each original character we add, record how many new NFC
        # characters it produced and map them all back to that original
        # index.
        nfc_to_orig = []
        prev_nfc_len = 0
        for orig_i in range(len(text)):
            cur_nfc_len = len(unicodedata.normalize('NFC', text[:orig_i + 1]))
            for _ in range(cur_nfc_len - prev_nfc_len):
                nfc_to_orig.append(orig_i)
            prev_nfc_len = cur_nfc_len

    # --- Phase 2: Remove zero-width characters with position tracking ----
    result_chars: list[str] = []
    result_to_orig: list[int] = []

    for nfc_i, ch in enumerate(nfc_text):
        if ch not in ZERO_WIDTH_CHARS:
            result_chars.append(ch)
            orig_pos = nfc_to_orig[nfc_i] if nfc_i < len(nfc_to_orig) else nfc_i
            result_to_orig.append(orig_pos)

    return (''.join(result_chars), result_to_orig)


def is_tibetan_numeral(char: str) -> bool:
    """
    Check if a character is a Tibetan digit or half-digit.

    Tibetan digits:      U+0F20–U+0F29  (༠–༩)
    Tibetan half-digits: U+0F2A–U+0F33  (༪–༳)

    These appear in text as numbers and should not be treated as
    spellable syllable content.
    """
    if not char:
        return False
    code = ord(char[0])
    return 0x0F20 <= code <= 0x0F33


def is_numeral_syllable(syllable: str) -> bool:
    """
    Return True if a syllable consists entirely of Tibetan numeral characters.

    Such syllables represent numbers (years, ordinals, counts) and should be
    skipped by the spellchecker without flagging an error.
    """
    if not syllable:
        return False
    return all(is_tibetan_numeral(c) for c in syllable)


def _is_spellable_tibetan_char(char: str) -> bool:
    """
    Return True if this character is a spellable Tibetan character — i.e. a
    base consonant, subjoined consonant, or vowel sign. Everything else in the
    Tibetan block (punctuation, marks, yig mgo openers, decorative shads, etc.)
    is non-spellable.

    Spellable ranges:
        U+0F40–U+0F6C  base consonants
        U+0F71–U+0F84  vowel signs (including AA, I, U, E, O and extensions)
        U+0F90–U+0FBC  subjoined consonants
    """
    code = ord(char)
    return (
        0x0F40 <= code <= 0x0F6C or
        0x0F71 <= code <= 0x0F84 or
        0x0F90 <= code <= 0x0FBC
    )


def is_punctuation_syllable(syllable: str) -> bool:
    """
    Return True if a syllable lies entirely within the Tibetan Unicode block
    but contains no spellable characters (no consonants or vowel signs).

    These are Tibetan punctuation and mark characters — yig mgo text openers
    (༄ ༅), decorative shad variants (༑ ༒), gter tsheg (༔), astrological
    marks, etc. — that appear in texts but carry no spelling content.
    """
    if not syllable:
        return False
    return (
        all(is_tibetan_char(c) for c in syllable) and
        not any(_is_spellable_tibetan_char(c) for c in syllable)
    )


def is_tibetan_char(char: str) -> bool:
    """Return True if the character is in the Tibetan Unicode block (U+0F00–U+0FFF)."""
    if not char:
        return False
    code = ord(char[0])
    return 0x0F00 <= code <= 0x0FFF


def extract_tibetan(text: str) -> str:
    """Filter text to Tibetan characters only (strips Latin, numerals, etc.)."""
    return ''.join(char for char in text if is_tibetan_char(char))


def validate_tibetan_text(text: str) -> Dict:
    """
    Validate text and count non-Tibetan characters (excluding whitespace).
    
    Returns a summary of non-Tibetan characters found, useful for informing
    users that some content was skipped during spell checking.
    
    Args:
        text: Text to validate
        
    Returns:
        Dictionary with summary of non-Tibetan characters:
        {
            'count': int,           # Number of non-Tibetan chars (excluding whitespace)
            'has_non_tibetan': bool # True if any non-Tibetan chars found
        }
    """
    non_tibetan_count = 0
    
    for char in text:
        if char.isspace():
            continue
        if not is_tibetan_char(char):
            non_tibetan_count += 1
    
    return {
        'count': non_tibetan_count,
        'has_non_tibetan': non_tibetan_count > 0
    }
