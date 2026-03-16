"""
Structural Completeness Checks

Checks that the parsed structure accounts for all characters.
This is a bridge function that works with the old dict-based parsed format.
"""
from typing import Dict, Optional


def check_syllable_structure_completeness(syllable: str, parsed: Dict[str, any]) -> Optional[Dict[str, any]]:
    """
    Check that the parsed structure accounts for all characters.

    This is a bridge function that works with the old dict-based parsed format.
    It will be simplified once the full pipeline uses TibetanSyllable.

    Returns the most fundamental error found.

    Args:
        syllable: The original syllable string
        parsed: The parsed structure dict

    Returns:
        None if valid, or error dict
    """
    errors_found = []

    # Count structural components in raw string
    base_consonants = []
    subjoined_consonants = []
    vowels = []

    for i, char in enumerate(syllable):
        code = ord(char)
        if 0x0F40 <= code <= 0x0F6C:
            base_consonants.append((i, char))
        elif 0x0F90 <= code <= 0x0FBC:
            subjoined_consonants.append((i, char))
        elif 0x0F71 <= code <= 0x0F7C:
            vowels.append((i, char))

    # ERROR 1: Multiple separated vowels
    if len(vowels) > 1:
        # Exception: འི relational suffix
        # When a syllable ends with འ + ི, the ི is a valid suffix vowel.
        # This creates exactly 2 vowel marks (root vowel + suffix ི) which
        # is legitimate and should not be flagged.
        is_achung_i_suffix = False
        if len(vowels) == 2:
            last_vowel_pos, last_vowel_char = vowels[-1]
            if (last_vowel_char == '\u0F72' and  # ི
                    last_vowel_pos > 0 and
                    last_vowel_pos - 1 < len(syllable) and
                    ord(syllable[last_vowel_pos - 1]) == 0x0F60):  # འ
                is_achung_i_suffix = True

        if not is_achung_i_suffix:
            vowel_positions = [pos for pos, _ in vowels]
            has_separated = any(
                vowel_positions[i + 1] - vowel_positions[i] > 1
                for i in range(len(vowel_positions) - 1)
            )
            if has_separated or len(vowels) > 2:
                errors_found.append({
                    'error_type': 'multiple_vowels',
                    'message': f'Syllable has {len(vowels)} vowels - a syllable can only have one vowel (or vowel combination like ོུ)',
                    'severity': 'error',
                    'component': 'structure',
                    'priority': 1
                })

    # ERROR 2: Subjoined consonant after vowel
    if subjoined_consonants and vowels:
        first_vowel_pos = vowels[0][0]
        for pos, char in subjoined_consonants:
            if pos > first_vowel_pos:
                errors_found.append({
                    'error_type': 'consonant_after_vowel',
                    'message': f'Structural consonant ({char}) appears after vowel - vowels must come after all consonant clusters',
                    'severity': 'error',
                    'component': 'structure',
                    'priority': 2
                })
                break

    # ERROR 3: Too many consonants after vowel
    if vowels and base_consonants:
        first_vowel_pos = vowels[0][0]
        consonants_after = [c for pos, c in base_consonants if pos > first_vowel_pos]

        expected = 0
        if parsed.get('suffix'):
            expected += 1
        if parsed.get('post_suffix'):
            expected += 1

        if len(consonants_after) > expected:
            errors_found.append({
                'error_type': 'unparsed_characters',
                'message': f'Syllable has {len(consonants_after)} consonants after vowel but only {expected} valid suffix position(s)',
                'severity': 'error',
                'component': 'structure',
                'priority': 3
            })

    # ERROR 4: Too many base consonants total
    if len(base_consonants) > 5:
        errors_found.append({
            'error_type': 'too_many_consonants',
            'message': f'Syllable has {len(base_consonants)} consonants - likely multiple syllables without tsheg separator',
            'severity': 'error',
            'component': 'structure',
            'priority': 4
        })

    # ERROR 5: Trailing consonants not parsed
    last_base_consonant = None
    last_base_pos = -1
    for i, char in enumerate(syllable):
        if 0x0F40 <= ord(char) <= 0x0F6C:
            last_base_consonant = char
            last_base_pos = i

    if last_base_consonant:
        suffix = parsed.get('suffix')
        post_suffix = parsed.get('post_suffix')

        if post_suffix:
            if last_base_consonant != post_suffix:
                errors_found.append({
                    'error_type': 'unparsed_characters',
                    'message': f'Trailing consonant {last_base_consonant} not accounted for in parsing',
                    'severity': 'error',
                    'component': 'structure',
                    'priority': 5
                })
        elif suffix:
            suffix_pos = syllable.rfind(suffix)
            if last_base_pos > suffix_pos:
                errors_found.append({
                    'error_type': 'invalid_post_suffix',
                    'message': f'Consonant {last_base_consonant} appears after suffix but is not a valid post-suffix (only ད or ས allowed)',
                    'severity': 'error',
                    'component': 'structure',
                    'priority': 5
                })

    # Return highest priority error
    if errors_found:
        errors_found.sort(key=lambda e: e.get('priority', 999))
        best = errors_found[0]
        del best['priority']
        return best

    return None
