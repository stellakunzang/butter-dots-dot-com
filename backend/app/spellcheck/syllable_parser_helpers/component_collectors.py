"""
Tibetan Syllable Component Collectors

Helper functions to collect multiple characters of the same type.
"""
from typing import Dict, List
from ..syllable_parser_helpers.character_utils import is_subjoined_consonant, is_vowel, is_base_consonant, is_post_suffix


def collect_subscripts(chars: list, start: int, end: int) -> List[str]:
    """
    Collect subscript consonants between start and end indices.
    
    Subscripts appear below the root consonant.
    
    Args:
        chars: Character list
        start: Start index (inclusive)
        end: End index (exclusive)
        
    Returns:
        List of subscript characters
    """
    subscripts = []
    for i in range(start, min(end, len(chars))):
        if is_subjoined_consonant(chars[i]):
            subscripts.append(chars[i])
    return subscripts


def collect_subscripts_simple(chars: list, start_index: int) -> Dict:
    """
    Collect all subscripts starting from index until non-subscript found.
    
    Returns: {'subscripts': list[str], 'next_index': int}
    """
    subscripts = []
    i = start_index
    while i < len(chars) and is_subjoined_consonant(chars[i]):
        subscripts.append(chars[i])
        i += 1
    return {'subscripts': subscripts, 'next_index': i}


def collect_vowels(chars: list, start_index: int) -> List[str]:
    """
    Collect all vowel marks starting from first vowel.
    
    Multiple vowels can appear together (though rare).
    
    Returns:
        List of vowel characters
    """
    vowels = []
    i = start_index
    while i < len(chars) and is_vowel(chars[i]):
        vowels.append(chars[i])
        i += 1
    return vowels


def collect_suffixes(chars: list, start_index: int) -> Dict:
    """
    Collect suffix and optional post-suffix.
    
    Tibetan allows:
    - Primary suffix (10 valid: ག ང ད ན བ མ འ ར ལ ས)
    - Post-suffix after primary suffix (2 valid: ད ས)
    
    Returns: {
        'suffix': str | None,
        'post_suffix': str | None
    }
    """
    result = {'suffix': None, 'post_suffix': None}
    
    if start_index >= len(chars):
        return result
    
    # Get primary suffix (next base consonant)
    if is_base_consonant(chars[start_index]):
        result['suffix'] = chars[start_index]
        
        # Get post-suffix (only if we have suffix, and only da or sa)
        if (start_index + 1 < len(chars) and 
            is_base_consonant(chars[start_index + 1]) and
            is_post_suffix(chars[start_index + 1])):
            result['post_suffix'] = chars[start_index + 1]
    
    return result
