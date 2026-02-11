"""
Tibetan Syllable Parser

Main parser for analyzing Tibetan syllable structure.

KEY PRINCIPLE: Vowels always attach to the root consonant.
The consonant immediately before the first vowel is the root.

Syllable structure:
    PREFIX + SUPERSCRIPT + ROOT + SUBSCRIPT(S) + VOWEL(S) + SUFFIX + POST-SUFFIX
"""
from typing import Dict
from .syllable_parser_helpers import (
    split_syllables,
    split_syllables_with_position,
    find_first_vowel,
    parse_with_vowels,
    parse_without_vowels,
    create_empty_result
)


class TibetanSyllableParser:
    """
    Parser for Tibetan syllable structure.
    
    Breaks down syllables into grammatical components for validation.
    Uses vowel position as the key to identifying the root consonant.
    """
    
    def parse(self, syllable: str) -> Dict[str, any]:
        """
        Parse a Tibetan syllable into its grammatical components.
        
        Strategy:
        1. Find first vowel (if present)
        2. If vowel exists: work backwards to identify root
        3. If no vowel: use consonant-based heuristics
        
        Args:
            syllable: Single Tibetan syllable (no tsheg)
            
        Returns:
            Dictionary with components:
            {
                'prefix': str | None,
                'superscript': str | None,
                'root': str,
                'subscripts': list[str],
                'vowels': list[str],
                'suffix': str | None,
                'post_suffix': str | None,
                'raw': str
            }
            
        Examples:
            བོད → {'root': 'བ', 'vowels': ['ོ'], 'suffix': 'ད'}
            དང → {'root': 'ད', 'suffix': 'ང'}
            བརྗེད → {'prefix': 'བ', 'superscript': 'ར', 'root': 'ཇ', 
                     'vowels': ['ེ'], 'suffix': 'ད'}
        """
        if not syllable:
            return create_empty_result("")
        
        chars = list(syllable)
        
        # Find vowel position (key to identifying root)
        first_vowel_index = find_first_vowel(chars)
        
        # Use appropriate parsing strategy
        if first_vowel_index is not None:
            # Has vowels - use vowel-based parsing
            return parse_with_vowels(chars, first_vowel_index, syllable)
        else:
            # No vowels - use consonant-based parsing
            return parse_without_vowels(chars, syllable)


# Re-export splitting functions for backwards compatibility
__all__ = ['TibetanSyllableParser', 'split_syllables', 'split_syllables_with_position']
