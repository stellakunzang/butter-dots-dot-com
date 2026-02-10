"""
Tibetan Syllable Parser

Parses Tibetan text into syllables and analyzes syllable structure.
Based on Unicode encoding analysis in /docs/research/UNICODE_ENCODING_RULES.md
"""
from typing import List, Dict, Optional


# Tibetan Unicode Ranges
TSHEG = '\u0F0B'  # ་ syllable separator
SHAD = '\u0F0D'   # ། sentence ending
DOUBLE_SHAD = '\u0F0E'  # ༎ topic ending
SPACE = '\u0F0C'  # ༌ non-breaking space

# Consonant ranges
BASE_CONSONANT_START = 0x0F40
BASE_CONSONANT_END = 0x0F6C
SUBJOINED_CONSONANT_START = 0x0F90
SUBJOINED_CONSONANT_END = 0x0FBC

# Vowel range
VOWEL_START = 0x0F71
VOWEL_END = 0x0F7C

# Import shared constants from rules module (DRY principle)
from app.spellcheck.rules import (
    VALID_PREFIXES,
    VALID_SUPERSCRIPTS, 
    VALID_POST_SUFFIXES,
    VALID_SUFFIXES
)


def split_syllables(text: str) -> List[str]:
    """
    Split Tibetan text into syllables by tsheg (་).
    
    Args:
        text: Tibetan text string
        
    Returns:
        List of syllable strings (without tsheg or punctuation)
    """
    # Remove or split on punctuation marks
    text = text.replace(SHAD, TSHEG)
    text = text.replace(DOUBLE_SHAD, TSHEG)
    text = text.replace(SPACE, TSHEG)
    
    # Split by tsheg
    syllables = text.split(TSHEG)
    
    # Filter out empty strings and whitespace
    syllables = [s.strip() for s in syllables if s.strip()]
    
    return syllables


def split_syllables_with_position(text: str) -> List[Dict[str, any]]:
    """
    Split Tibetan text into syllables with character position tracking.
    
    Args:
        text: Tibetan text string
        
    Returns:
        List of dicts with 'syllable' and 'position' keys
    """
    result = []
    current_pos = 0
    current_syllable = ""
    
    for i, char in enumerate(text):
        if char in [TSHEG, SHAD, DOUBLE_SHAD, SPACE, ' ', '\t', '\n']:
            if current_syllable:
                result.append({
                    'syllable': current_syllable,
                    'position': current_pos
                })
                current_syllable = ""
                current_pos = i + 1
        else:
            if not current_syllable:
                current_pos = i
            current_syllable += char
    
    # Don't forget last syllable if no trailing separator
    if current_syllable:
        result.append({
            'syllable': current_syllable,
            'position': current_pos
        })
    
    return result


def is_base_consonant(char: str) -> bool:
    """Check if character is a base consonant (U+0F40-0F6C)"""
    if not char:
        return False
    return BASE_CONSONANT_START <= ord(char) <= BASE_CONSONANT_END


def is_subjoined_consonant(char: str) -> bool:
    """Check if character is a subjoined consonant (U+0F90-0FBC)"""
    if not char:
        return False
    return SUBJOINED_CONSONANT_START <= ord(char) <= SUBJOINED_CONSONANT_END


def is_vowel(char: str) -> bool:
    """Check if character is a vowel mark (U+0F71-0F7C)"""
    if not char:
        return False
    return VOWEL_START <= ord(char) <= VOWEL_END


def is_prefix(char: str) -> bool:
    """Check if character is one of the 5 valid prefixes"""
    return char in VALID_PREFIXES


def is_superscript(char: str) -> bool:
    """Check if character is one of the 3 valid superscripts"""
    return char in VALID_SUPERSCRIPTS


def is_post_suffix(char: str) -> bool:
    """Check if character is a valid post-suffix (only da or sa)"""
    return char in VALID_POST_SUFFIXES


def subjoined_to_base(char: str) -> str:
    """
    Convert subjoined consonant (U+0F90-0FBC) to base consonant (U+0F40-0F6C).
    
    Subjoined consonants are used below superscripts but represent the same
    letters as base consonants. For validation, we need the base form.
    
    Examples:
        ྐ (U+0F90) → ཀ (U+0F40) ka
        ྲ (U+0FB2) → ར (U+0F62) ra
    """
    if not char or not is_subjoined_consonant(char):
        return char
    
    # Calculate offset: subjoined start - base start = 0x0F90 - 0x0F40 = 0x50
    offset = SUBJOINED_CONSONANT_START - BASE_CONSONANT_START
    base_code = ord(char) - offset
    
    # Return base consonant
    return chr(base_code)


class TibetanSyllableParser:
    """
    Parser for Tibetan syllable structure.
    
    Breaks down syllables into components:
    PREFIX + SUPERSCRIPT + ROOT + SUBSCRIPT + VOWEL + SUFFIX + POST-SUFFIX
    """
    
    def parse(self, syllable: str) -> Dict[str, any]:
        """
        Parse a single Tibetan syllable into its components.
        
        Based on Unicode encoding rules:
        - BASE consonants (U+0F40-0F6C): prefix, superscript, suffix, post-suffix, standalone root
        - SUBJOINED consonants (U+0F90-0FBC): root under superscript, subscripts
        
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
                'raw': str  # original syllable
            }
        """
        if not syllable:
            return self._empty_result("")
        
        chars = list(syllable)
        i = 0
        
        result = {
            'prefix': None,
            'superscript': None,
            'root': None,
            'subscripts': [],
            'vowels': [],
            'suffix': None,
            'post_suffix': None,
            'raw': syllable
        }
        
        # 1. Check for PREFIX vs ROOT
        # CRITICAL RULES:
        #   - Base consonant + subjoined WITHOUT prefix first = ROOT + SUBSCRIPT
        #   - Base consonant + subjoined WITH prefix first = might be SUPERSCRIPT
        #   - For 2 base consonants: check if 2nd is valid suffix
        # 
        # Examples:
        #   སྲ = ས (root) + ྲ (subscript) - NO prefix, so ས is root!
        #   བསྒྲ = བ (prefix) + ས (superscript) + ྒ (root) + ྲ (subscript)
        #   དང = ད (root) + ང (suffix)
        #   གཡ = ག (prefix) + ཡ (root)
        
        if i < len(chars) and is_base_consonant(chars[i]):
            if i + 1 < len(chars):
                # Check what follows to determine role
                # NOTE: Don't check for superscript here - only prefixes at the start!
                # Superscripts only appear AFTER a prefix
                if is_base_consonant(chars[i + 1]) and is_prefix(chars[i]):
                    # Check if this is truly a prefix situation
                    # For 2-letter case: check if 2nd letter is a valid suffix
                    # If it IS a valid suffix → 1st is root, not prefix
                    # If it's NOT a valid suffix → 1st is prefix
                    
                    has_more_structure = (
                        i + 2 < len(chars) or  # 3+ consonants
                        any(is_subjoined_consonant(c) for c in chars[i+1:]) or  # Has subscripts
                        any(is_vowel(c) for c in chars[i+1:i+3])  # Has vowels between first two
                    )
                    
                    # For 2-letter case with no additional structure
                    if not has_more_structure:
                        # Check if 2nd letter is a valid suffix
                        second_letter = chars[i + 1]
                        if second_letter in VALID_SUFFIXES:
                            # 2nd is valid suffix → 1st is root (not prefix)
                            # Will be parsed as root + suffix
                            pass  # Continue to root parsing
                        else:
                            # 2nd is NOT valid suffix → 1st is prefix, 2nd is root
                            result['prefix'] = chars[i]
                            i += 1
                    else:
                        # 3+ letters or has structure → 1st is prefix
                        result['prefix'] = chars[i]
                        i += 1
                # else: it's the root itself (standalone)
        
        # 2. Check for SUPERSCRIPT after PREFIX
        # After consuming a prefix, we might have a superscript next
        if result['prefix'] and i < len(chars) and is_base_consonant(chars[i]):
            if i + 1 < len(chars) and is_subjoined_consonant(chars[i + 1]) and is_superscript(chars[i]):
                # This is a superscript (e.g., བསྒྲུབ: prefix བ, superscript ས, root ྒ)
                result['superscript'] = chars[i]
                i += 1
        
        # 3. Get ROOT
        if i < len(chars):
            if is_subjoined_consonant(chars[i]):
                # Root is in subjoined form (below superscript)
                # Convert to base form for validation
                result['root'] = subjoined_to_base(chars[i])
                i += 1
            elif is_base_consonant(chars[i]):
                # Standalone root (no superscript)
                result['root'] = chars[i]
                i += 1
        
        # 4. Collect SUBSCRIPTS (any remaining subjoined consonants)
        while i < len(chars) and is_subjoined_consonant(chars[i]):
            result['subscripts'].append(chars[i])
            i += 1
        
        # 5. Collect VOWELS
        while i < len(chars) and is_vowel(chars[i]):
            result['vowels'].append(chars[i])
            i += 1
        
        # 6. Get SUFFIX (next base consonant)
        if i < len(chars) and is_base_consonant(chars[i]):
            result['suffix'] = chars[i]
            i += 1
        
        # 7. Get POST-SUFFIX (only if we have a suffix, and only da or sa)
        if result['suffix'] and i < len(chars):
            if is_base_consonant(chars[i]) and is_post_suffix(chars[i]):
                result['post_suffix'] = chars[i]
                i += 1
        
        return result
    
    def _empty_result(self, syllable: str) -> Dict[str, any]:
        """Return empty parse result"""
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
    
    def get_root_letter(self, parsed: Dict[str, any]) -> Optional[str]:
        """
        Extract the root letter from parsed syllable.
        
        Args:
            parsed: Result from parse()
            
        Returns:
            Root letter (may be in subjoined form)
        """
        return parsed.get('root')
    
    def has_prefix(self, parsed: Dict[str, any]) -> bool:
        """Check if syllable has a prefix"""
        return parsed.get('prefix') is not None
    
    def has_superscript(self, parsed: Dict[str, any]) -> bool:
        """Check if syllable has a superscript"""
        return parsed.get('superscript') is not None
    
    def has_subscripts(self, parsed: Dict[str, any]) -> bool:
        """Check if syllable has any subscripts"""
        return len(parsed.get('subscripts', [])) > 0
    
    def has_suffix(self, parsed: Dict[str, any]) -> bool:
        """Check if syllable has a suffix"""
        return parsed.get('suffix') is not None
    
    def count_components(self, parsed: Dict[str, any]) -> int:
        """
        Count how many components are present in the syllable.
        
        Returns:
            Integer 1-7 (root is always required, so minimum is 1)
        """
        count = 0
        if parsed.get('prefix'): count += 1
        if parsed.get('superscript'): count += 1
        if parsed.get('root'): count += 1
        if parsed.get('subscripts'): count += len(parsed['subscripts'])
        if parsed.get('vowels'): count += len(parsed['vowels'])
        if parsed.get('suffix'): count += 1
        if parsed.get('post_suffix'): count += 1
        return count
