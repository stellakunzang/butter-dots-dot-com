"""
Pattern-based Validation

Checks raw syllable strings for pattern-based issues.
These checks run BEFORE parsing: encoding errors, length, unusual marks.
"""
from typing import Dict, Optional


def check_syllable_patterns(syllable: str) -> Optional[Dict[str, any]]:
    """
    Check raw syllable string for pattern-based issues.

    These checks run BEFORE parsing: encoding errors, length, unusual marks.

    Args:
        syllable: Raw Tibetan syllable string

    Returns:
        None if valid, or error dict if issue found
    """
    # Check if syllable is too long (8+ Tibetan characters is suspicious)
    tibetan_chars = [c for c in syllable if 0x0F00 <= ord(c) <= 0x0FFF]
    if len(tibetan_chars) >= 8:
        return {
            'error_type': 'syllable_too_long',
            'message': f'Syllable has {len(tibetan_chars)} characters (suspicious)',
            'severity': 'error',
            'component': 'pattern'
        }

    # Check for wrong 'a' character (U+0FB0 instead of U+0F71)
    if '\u0FB0' in syllable:
        return {
            'error_type': 'encoding_error',
            'message': 'Wrong "a" character (U+0FB0 instead of U+0F71)',
            'severity': 'critical',
            'component': 'encoding'
        }

    # Check for wrong ra (U+0F6A instead of U+0F62)
    if '\u0F6A' in syllable:
        return {
            'error_type': 'encoding_error',
            'message': 'Wrong ra character (U+0F6A instead of U+0F62)',
            'severity': 'critical',
            'component': 'encoding'
        }

    # Check for double vowels (two consecutive vowel marks)
    for i in range(len(syllable) - 1):
        if (0x0F71 <= ord(syllable[i]) <= 0x0F7C and
                0x0F71 <= ord(syllable[i + 1]) <= 0x0F7C):
            return {
                'error_type': 'double_vowel',
                'message': 'Double vowel marks are invalid',
                'severity': 'error',
                'component': 'pattern'
            }

    # Check for unusual marks (TSA-PHRU followed by consonant)
    for i, char in enumerate(syllable):
        code = ord(char)
        if code == 0x0F39:
            if i + 1 < len(syllable):
                next_code = ord(syllable[i + 1])
                if 0x0F40 <= next_code <= 0x0F6C:
                    return {
                        'error_type': 'unusual_mark_position',
                        'message': 'TSA-PHRU mark (\u0F39) followed by additional consonants - this creates an invalid syllable structure',
                        'severity': 'error',
                        'component': 'pattern'
                    }

    return None
