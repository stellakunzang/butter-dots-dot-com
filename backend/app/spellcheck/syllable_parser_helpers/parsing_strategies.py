"""
Tibetan Syllable Parsing Strategies

Different strategies for parsing syllables based on their structure.
"""
from typing import Dict
from ..syllable_parser_helpers.character_utils import is_vowel
from ..syllable_parser_helpers.component_identifiers import (
    identify_prefix,
    identify_superscript,
    identify_root,
    identify_root_complex_from_vowel
)
from ..syllable_parser_helpers.component_collectors import (
    collect_subscripts,
    collect_subscripts_simple,
    collect_vowels,
    collect_suffixes
)


def find_first_vowel(chars: list) -> int | None:
    """
    Find index of first vowel mark in character list.
    
    Vowels are key to identifying roots since they always attach to roots.
    """
    for idx, char in enumerate(chars):
        if is_vowel(char):
            return idx
    return None


def parse_with_vowels(chars: list, vowel_index: int, syllable: str) -> Dict:
    """
    Parse syllable that contains vowels.
    
    Strategy: Work backwards from vowel to find root and its modifiers.
    Vowels always attach to the root, so the consonant before the vowel
    is the root.
    
    Example: བོད (bod = Tibet)
        - བ before vowel ོ → བ is root
        - ད after vowel → ད is suffix
    """
    result = create_empty_result(syllable)
    
    # Find the root by working backwards from vowel
    root_complex = identify_root_complex_from_vowel(chars, vowel_index)
    result.update(root_complex)
    
    # Collect subscripts after root (before vowel)
    subscript_start = root_complex['next_index']
    result['subscripts'] = collect_subscripts(chars, subscript_start, vowel_index)
    
    # Collect vowels
    result['vowels'] = collect_vowels(chars, vowel_index)
    
    # Collect suffix and post-suffix after vowels
    suffix_start = vowel_index + len(result['vowels'])
    suffixes = collect_suffixes(chars, suffix_start)
    result['suffix'] = suffixes['suffix']
    result['post_suffix'] = suffixes['post_suffix']
    
    return result


def parse_without_vowels(chars: list, syllable: str) -> Dict:
    """
    Parse syllable without vowels (consonant-only).
    
    Strategy: Check for prefix, then superscript, then root, then suffixes.
    Common for short words like དང (dang) = root + suffix.
    
    Example: དང (dang = and)
        - No vowel present
        - ད could be prefix or root
        - ང is valid suffix → so ད is root, not prefix
    """
    result = create_empty_result(syllable)
    i = 0
    
    # Check for prefix
    prefix_result = identify_prefix(chars, i)
    result['prefix'] = prefix_result['prefix']
    i = prefix_result['next_index']
    
    # Check for superscript (only after prefix)
    if result['prefix']:
        superscript_result = identify_superscript(chars, i)
        result['superscript'] = superscript_result['superscript']
        i = superscript_result['next_index']
    
    # Get root
    root_result = identify_root(chars, i)
    result['root'] = root_result['root']
    i = root_result['next_index']
    
    # Collect subscripts
    subscripts_result = collect_subscripts_simple(chars, i)
    result['subscripts'] = subscripts_result['subscripts']
    i = subscripts_result['next_index']
    
    # Get suffix and post-suffix
    suffixes = collect_suffixes(chars, i)
    result['suffix'] = suffixes['suffix']
    result['post_suffix'] = suffixes['post_suffix']
    
    return result


def create_empty_result(syllable: str) -> Dict:
    """Create empty parse result structure."""
    return {
        'prefix': None,
        'superscript': None,
        'root': None,
        'subscripts': [],
        'vowels': [],
        'suffix': None,
        'post_suffix': None,
        'raw': syllable
    }
