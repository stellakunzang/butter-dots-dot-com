"""
Tibetan Syllable Component Identifiers

Helper functions to identify specific grammatical components in syllables.
"""
from typing import Dict
from ..syllable_parser_helpers.character_utils import (
    is_base_consonant,
    is_subjoined_consonant,
    is_prefix,
    is_superscript,
    is_post_suffix
)
from ..syllable_parser_helpers.unicode_utils import subjoined_to_base
from app.spellcheck.rules import VALID_SUFFIXES


def identify_prefix(chars: list, start_index: int) -> Dict:
    """
    Identify prefix consonant if present.
    
    Returns: {'prefix': str | None, 'next_index': int}
    """
    if start_index >= len(chars):
        return {'prefix': None, 'next_index': start_index}
    
    if not is_base_consonant(chars[start_index]):
        return {'prefix': None, 'next_index': start_index}
    
    # Check if this could be a prefix
    if start_index + 1 < len(chars):
        if is_base_consonant(chars[start_index + 1]) and is_prefix(chars[start_index]):
            # Determine if it's truly a prefix or just a root
            has_structure = (
                start_index + 2 < len(chars) or
                any(is_subjoined_consonant(c) for c in chars[start_index + 1:])
            )
            
            # For 2-letter case: check if 2nd is valid suffix
            if not has_structure:
                if chars[start_index + 1] in VALID_SUFFIXES:
                    # It's root + suffix, not prefix + root
                    return {'prefix': None, 'next_index': start_index}
                else:
                    # It's prefix + root
                    return {'prefix': chars[start_index], 'next_index': start_index + 1}
            else:
                # Has more structure - it's a prefix
                return {'prefix': chars[start_index], 'next_index': start_index + 1}
    
    return {'prefix': None, 'next_index': start_index}


def identify_superscript(chars: list, start_index: int) -> Dict:
    """
    Identify superscript consonant if present.
    
    Superscripts appear above the root and are followed by subjoined consonants.
    
    Returns: {'superscript': str | None, 'next_index': int}
    """
    if start_index >= len(chars):
        return {'superscript': None, 'next_index': start_index}
    
    if not is_base_consonant(chars[start_index]):
        return {'superscript': None, 'next_index': start_index}
    
    # Superscript followed by subjoined consonant (root)
    if (start_index + 1 < len(chars) and 
        is_subjoined_consonant(chars[start_index + 1]) and
        is_superscript(chars[start_index])):
        return {'superscript': chars[start_index], 'next_index': start_index + 1}
    
    return {'superscript': None, 'next_index': start_index}


def identify_root(chars: list, start_index: int) -> Dict:
    """
    Identify root consonant.
    
    Root can be in base form or subjoined form (below superscript).
    
    Returns: {'root': str | None, 'next_index': int}
    """
    if start_index >= len(chars):
        return {'root': None, 'next_index': start_index}
    
    if is_subjoined_consonant(chars[start_index]):
        # Root in subjoined form (below superscript)
        return {
            'root': subjoined_to_base(chars[start_index]),
            'next_index': start_index + 1
        }
    elif is_base_consonant(chars[start_index]):
        # Standalone root (no superscript)
        return {
            'root': chars[start_index],
            'next_index': start_index + 1
        }
    
    return {'root': None, 'next_index': start_index}


def identify_root_complex_from_vowel(chars: list, vowel_index: int) -> Dict:
    """
    Identify root and its modifiers by working backwards from vowel position.
    
    The consonant immediately before the vowel is the root.
    Works backwards to find prefix and superscript if present.
    
    Returns: {
        'prefix': str | None,
        'superscript': str | None,
        'root': str | None,
        'next_index': int
    }
    """
    result = {'prefix': None, 'superscript': None, 'root': None, 'next_index': 0}
    
    # Work backwards from vowel to find root
    # The consonant immediately before vowel is the root
    root_index = vowel_index - 1
    
    # Identify root
    if is_subjoined_consonant(chars[root_index]):
        # Root is subjoined - there MUST be a superscript before it
        result['root'] = subjoined_to_base(chars[root_index])
        
        # Look for superscript (base consonant before subjoined root)
        if root_index > 0 and is_base_consonant(chars[root_index - 1]):
            result['superscript'] = chars[root_index - 1]
            
            # Check for prefix before superscript
            if root_index > 1 and is_base_consonant(chars[root_index - 2]):
                result['prefix'] = chars[root_index - 2]
        
        # Next index is after the root
        result['next_index'] = root_index + 1
        
    elif is_base_consonant(chars[root_index]):
        # Root is in base form (no superscript)
        result['root'] = chars[root_index]
        
        # Check for prefix before root
        if root_index > 0 and is_base_consonant(chars[root_index - 1]):
            result['prefix'] = chars[root_index - 1]
        
        # Next index is after the root
        result['next_index'] = root_index + 1
    
    return result
