"""
Tibetan Spell Check Engine

Main spell checking engine that integrates normalization, parsing, and rules.
"""
from typing import List, Dict, Optional
from .normalizer import normalize_tibetan, is_tibetan_char
from .syllable_parser import split_syllables_with_position
from .rules import (
    validate_syllable_structure,
    check_syllable_patterns,
    get_error_severity
)


class TibetanSpellChecker:
    """
    Main Tibetan spell checking engine.
    
    Integrates Unicode normalization, syllable parsing, and grammatical rules
    to check Tibetan text for spelling errors.
    """
    
    def __init__(self):
        """Initialize the spell checker."""
        # Engine is ready to use - rules are in the rules module
        pass
    
    def check_syllable(self, syllable: str) -> Optional[Dict]:
        """
        Check a single syllable for spelling errors.
        
        Args:
            syllable: Tibetan syllable to check
            
        Returns:
            Dictionary with error details if error found, None if valid:
            {
                'word': str,
                'error_type': str,
                'severity': str ('critical', 'error', or 'info')
            }
        """
        # Normalize the syllable
        syllable = normalize_tibetan(syllable)
        
        if not syllable:
            return None
        
        # Check pattern-based rules (too long, double vowels, etc.)
        pattern_error = check_syllable_patterns(syllable)
        if pattern_error:
            # Add word to error dict and return
            pattern_error['word'] = syllable
            return pattern_error
        
        # Check structural rules (prefix, superscript, subscript, suffix)
        structure_error = validate_syllable_structure(syllable)
        if structure_error:
            # Add word to error dict and return
            structure_error['word'] = syllable
            return structure_error
        
        # No errors found
        return None
    
    def check_text(self, text: str) -> List[Dict]:
        """
        Check full Tibetan text for spelling errors.
        
        Args:
            text: Tibetan text to check
            
        Returns:
            List of error dictionaries, each with:
            {
                'word': str,           # The problematic syllable
                'position': int,       # Character position in text
                'error_type': str,     # Type of error
                'severity': str        # 'critical', 'error', or 'info'
            }
        
        Raises:
            TypeError: If text is None
        """
        if text is None:
            raise TypeError("text cannot be None")
        
        if not text:
            return []
        
        # Normalize text
        text = normalize_tibetan(text)
        
        # Split into syllables with position tracking
        syllables = split_syllables_with_position(text)
        
        # Check each syllable (skip non-Tibetan syllables)
        errors = []
        for item in syllables:
            syllable = item['syllable']
            
            # Skip if syllable has no Tibetan characters
            if not any(is_tibetan_char(c) for c in syllable):
                continue
            
            error = self.check_syllable(syllable)
            if error:
                # Add position information
                error['position'] = item['position']
                errors.append(error)
        
        return errors
