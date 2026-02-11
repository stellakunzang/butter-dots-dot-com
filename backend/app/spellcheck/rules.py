"""
Tibetan Spelling Rules Validator

Validates Tibetan syllable components against grammatical rules.
Based on traditional Tibetan grammar rules and linguistic research.
References: /docs/research/PREFIX_RULES_REFERENCE.md
"""
from typing import Dict, Optional, Union


# The 6 valid prefixes (including 'a-chung)
VALID_PREFIXES = {'ག', 'ད', 'བ', 'མ', 'འ', 'ར'}  # ga, da, ba, ma, 'a, ra

# The 3 valid superscripts
VALID_SUPERSCRIPTS = {'ར', 'ལ', 'ས'}  # ra-mgo, la-mgo, sa-mgo

# The 4 valid subscripts (in subjoined form)
VALID_SUBSCRIPTS = {'\u0FB1', '\u0FB2', '\u0FB3', '\u0FAD'}  # ya, ra, la, wa

# The 10 valid suffixes
VALID_SUFFIXES = {'ག', 'ང', 'ད', 'ན', 'བ', 'མ', 'འ', 'ར', 'ལ', 'ས'}

# The 2 valid post-suffixes
VALID_POST_SUFFIXES = {'ད', 'ས'}  # da, sa


# VALID stacks from authoritative list (see /docs/research/VALID_STACKS_REFERENCE.md)
# Using POSITIVE validation (what IS valid) rather than exclusive pattern matching

# Roots that CAN take wa-zur (ྭ) subscript
VALID_WA_ZUR_ROOTS = {
    'ཀ', 'ཁ', 'ག', 'ཅ', 'ཉ', 'ཏ', 'ད', 'ཙ', 'ཚ', 'ཞ', 'ཟ', 'ར', 'ཤ', 'ས', 'ཧ'
}

# Roots that CAN take ya-btags (ྱ) subscript
VALID_YA_BTAGS_ROOTS = {
    'ཀ', 'ཁ', 'ག', 'པ', 'ཕ', 'བ', 'མ'
}

# Roots that CAN take ra-btags (ྲ) subscript  
VALID_RA_BTAGS_ROOTS = {
    'ཀ', 'ཁ', 'ག', 'ཏ', 'ཐ', 'ད', 'པ', 'ཕ', 'བ', 'མ', 'ཤ', 'ས', 'ཧ'
}

# Roots that CAN take la-btags (ླ) subscript
VALID_LA_BTAGS_ROOTS = {
    'ཀ', 'ག', 'བ', 'ཟ', 'ར', 'ས'
}

# Roots that CAN have ra-mgo (ར) superscript
VALID_RA_MGO_ROOTS = { 
    'ཀ', 'ག', 'ང', 'ཇ', 'ཉ', 'ཏ', 'ད', 'ན', 'བ', 'མ', 'ཙ', 'ཛ'
}

# Roots that CAN have la-mgo (ལ) superscript
VALID_LA_MGO_ROOTS = {
    'ཀ', 'ག', 'ང', 'ཅ', 'ཇ', 'ཏ', 'ད', 'པ', 'བ', 'ཧ'
}

# Roots that CAN have sa-mgo (ས) superscript
VALID_SA_MGO_ROOTS = {
    'ཀ', 'ག', 'ང', 'ཉ', 'ཏ', 'ད', 'ན', 'པ', 'བ', 'མ', 'ཙ'
}


# NOTE: Using POSITIVE validation (valid lists above) instead of negative pattern matching
# This is more accurate based on authoritative Tibetan valid stacks list


# Invalid prefix + root combinations
# These are the combinations that are EXPLICITLY INVALID
INVALID_PREFIX_COMBOS = {
    'ག': {  # ga prefix cannot prefix these roots
        'ཀ',  # ka
        'ཁ',  # kha
        'ཆ',  # cha
        'ཇ',  # ja
        'ཐ',  # tha
        'ཚ',  # tsa
        'པ',  # pa
        'ཕ',  # pha
        'ཛ',  # dza
        'ཝ',  # wa
        'ཧ',  # ha
    },
    'ད': {  # da prefix cannot prefix these roots
        'ཁ',  # kha
        'ང',  # nga
        'ཅ',  # ca
        'ཆ',  # cha
        'ཇ',  # ja
        'ཉ',  # nya
        'ཐ',  # tha
        'ཕ',  # pha
        'ཙ',  # tsa
        'ཚ',  # tsa
        'ཛ',  # dza
        'ཝ',  # wa
        'ཞ',  # zha
        'ཟ',  # za
        'ཡ',  # ya
        'ལ',  # la
        'ཧ',  # ha
    },
    'བ': {  # ba prefix cannot prefix these roots
        'ཁ',  # kha
        'ཆ',  # cha
        'ཇ',  # ja
        'ཉ',  # nya
        'ཐ',  # tha
        'པ',  # pa
        'ཕ',  # pha
        'ཚ',  # tsa
        'ཛ',  # dza
        'ཝ',  # wa
        'ཡ',  # ya
        'ཧ',  # ha
    },
    'མ': {  # ma prefix cannot prefix these roots
        'ཀ',  # ka
        'ཅ',  # ca
        'ཏ',  # ta
        'པ',  # pa
        'ཕ',  # pha
        'ཙ',  # tsa
        'ཝ',  # wa
        'ཞ',  # zha
        'ཟ',  # za
        'ཡ',  # ya
        'ལ',  # la
        'ཧ',  # ha
    },
    'ར': {  # ra prefix cannot prefix these roots
        'ཀ',  # ka
        'ཅ',  # ca
        'ཉ',  # nya
        'པ',  # pa
        'ཏ',  # ta
        'ཙ',  # tsa
        'ཞ',  # zha
        'ཟ',  # za
        'ཡ',  # ya
        'ལ',  # la
        'ཝ',  # wa
        'ཧ',  # ha
    },
}


def is_valid_prefix_combination(prefix: str, root: str) -> bool:
    """
    Check if a prefix + root combination is valid.
    
    Uses "exclusive" checking:
    - If combination is in the invalid list → False
    - Otherwise → True
    
    Args:
        prefix: The prefix character
        root: The root character (may be base or subjoined form)
        
    Returns:
        True if valid, False if invalid
    """
    # Handle empty strings
    if not prefix or not root:
        return False
    
    # First check if it's even a valid prefix
    if prefix not in VALID_PREFIXES:
        return False
    
    # If root is in subjoined form, convert to base for checking
    # Subjoined = Base + 0x50
    root_codepoint = ord(root)
    if 0x0F90 <= root_codepoint <= 0x0FBC:
        # Convert subjoined to base form for rule checking
        base_root = chr(root_codepoint - 0x50)
    else:
        base_root = root
    
    # Check if this specific combination is invalid
    if prefix in INVALID_PREFIX_COMBOS:
        if base_root in INVALID_PREFIX_COMBOS[prefix]:
            return False
    
    return True


def is_valid_superscript_combination(superscript: str, root: str) -> bool:
    """
    Check if a superscript + root combination is valid.
    
    Uses positive validation from authoritative valid stacks list.
    
    Args:
        superscript: The superscript character (base form)
        root: The root character (can be base or subjoined form)
        
    Returns:
        True if valid, False if invalid
    """
    # Check if it's a valid superscript
    if superscript not in VALID_SUPERSCRIPTS:
        return False
    
    # Convert subjoined form root to base for checking against valid list
    root_codepoint = ord(root)
    if 0x0F90 <= root_codepoint <= 0x0FBC:
        # Convert subjoined to base form
        root_base = chr(root_codepoint - 0x50)
    else:
        # Already in base form
        root_base = root
    
    # Check against positive valid lists
    if superscript == 'ར':  # ra-mgo
        return root_base in VALID_RA_MGO_ROOTS
    elif superscript == 'ལ':  # la-mgo
        return root_base in VALID_LA_MGO_ROOTS
    elif superscript == 'ས':  # sa-mgo
        return root_base in VALID_SA_MGO_ROOTS
    
    return False


def is_valid_subscript_combination(root: str, subscript: str) -> bool:
    """
    Check if a root + subscript combination is valid.
    
    Uses positive validation from authoritative valid stacks list.
    
    Args:
        root: The root character (can be base or subjoined form)
        subscript: The subscript character (should be in subjoined form)
        
    Returns:
        True if valid, False if invalid
    """
    # Check if it's a valid subscript
    if subscript not in VALID_SUBSCRIPTS:
        return False
    
    # Convert subjoined root to base for checking against valid list
    root_codepoint = ord(root)
    if 0x0F90 <= root_codepoint <= 0x0FBC:
        # Convert subjoined to base form
        root_base = chr(root_codepoint - 0x50)
    else:
        # Already in base form
        root_base = root
    
    # Check against positive valid lists
    if subscript == '\u0FB1':  # ya-btags
        return root_base in VALID_YA_BTAGS_ROOTS
    elif subscript == '\u0FB2':  # ra-btags
        return root_base in VALID_RA_BTAGS_ROOTS
    elif subscript == '\u0FB3':  # la-btags
        return root_base in VALID_LA_BTAGS_ROOTS
    elif subscript == '\u0FAD':  # wa-zur
        return root_base in VALID_WA_ZUR_ROOTS
    
    return False


def is_valid_suffix(suffix: str) -> bool:
    """
    Check if a character is a valid suffix.
    
    Args:
        suffix: The suffix character
        
    Returns:
        True if it's one of the 10 valid suffixes
    """
    return suffix in VALID_SUFFIXES


def is_valid_post_suffix(post_suffix: str) -> bool:
    """
    Check if a character is a valid post-suffix.
    
    Args:
        post_suffix: The post-suffix character
        
    Returns:
        True if it's da or sa
    """
    return post_suffix in VALID_POST_SUFFIXES


def parse_syllable_structure(syllable: str) -> Dict[str, any]:
    """
    Parse a syllable into its components.
    Helper function that wraps TibetanSyllableParser.
    
    Args:
        syllable: Tibetan syllable string
        
    Returns:
        Dict with components (prefix, base/root, subscript, suffix, etc.)
    """
    from app.spellcheck.syllable_parser import TibetanSyllableParser
    parser = TibetanSyllableParser()
    parsed = parser.parse(syllable)
    
    # Get the root - may be in subjoined form if under superscript
    root = parsed.get('root')
    
    # Convert subjoined root to base form for 'base' field
    # (for backwards compatibility with tests expecting base form)
    if root:
        root_codepoint = ord(root)
        if 0x0F90 <= root_codepoint <= 0x0FBC:
            # Convert subjoined to base
            base = chr(root_codepoint - 0x50)
        else:
            base = root
    else:
        base = None
    
    # Map to expected key names for backwards compatibility
    return {
        'prefix': parsed.get('prefix'),
        'superscript': parsed.get('superscript'),
        'base': base,  # Base form (converted from subjoined if needed)
        'root': parsed.get('root'),  # Original root (may be subjoined)
        'subscript': parsed.get('subscripts', [])[0] if parsed.get('subscripts') else None,
        'subscripts': parsed.get('subscripts', []),
        'vowels': parsed.get('vowels', []),
        'suffix': parsed.get('suffix'),
        'post_suffix': parsed.get('post_suffix'),
        'raw': parsed.get('raw'),
    }


def get_error_severity(error_type: str) -> str:
    """
    Map error types to severity levels.
    
    Args:
        error_type: The type of error
        
    Returns:
        Severity level: 'critical', 'error', 'warning', or 'info'
    """
    severity_map = {
        'encoding_error': 'critical',
        'wrong_unicode': 'critical',
        'invalid_prefix': 'error',
        'invalid_prefix_combination': 'error',
        'invalid_superscript': 'error',
        'invalid_superscript_combination': 'error',
        'invalid_subscript': 'error',
        'invalid_subscript_combination': 'error',
        'invalid_suffix': 'error',
        'invalid_post_suffix': 'error',
        'syllable_too_long': 'error',
        'missing_root': 'error',
        'post_suffix_without_suffix': 'error',
        'sanskrit_marker': 'info',
        'foreign_transliteration': 'info',
    }
    return severity_map.get(error_type, 'warning')


def validate_syllable_structure(syllable_or_parsed: Union[str, Dict[str, any]]) -> Optional[Dict[str, any]]:
    """
    Validate a syllable structure against Tibetan grammar rules.
    
    Args:
        syllable_or_parsed: Either a syllable string or parsed dict from TibetanSyllableParser
        
    Returns:
        None if valid, or error dict if invalid:
        {
            'error_type': str,
            'message': str,
            'severity': str,  # 'error', 'warning', 'info'
            'component': str  # which component failed
        }
    """
    # Handle both string and parsed dict inputs
    if isinstance(syllable_or_parsed, str):
        parsed = parse_syllable_structure(syllable_or_parsed)
    else:
        parsed = syllable_or_parsed
    # 1. Root is required
    if not parsed.get('root'):
        return {
            'error_type': 'missing_root',
            'message': 'Syllable must have a root letter',
            'severity': 'error',
            'component': 'root'
        }
    
    # 2. Validate prefix + root combination
    # NOTE: Skip prefix validation if there's a superscript between prefix and root
    # because different combination rules apply with superscripts
    if parsed.get('prefix') and parsed.get('root') and not parsed.get('superscript'):
        if not is_valid_prefix_combination(parsed['prefix'], parsed['root']):
            return {
                'error_type': 'invalid_prefix_combination',
                'message': f"Prefix '{parsed['prefix']}' cannot prefix root '{parsed['root']}'",
                'severity': 'error',
                'component': 'prefix'
            }
    
    # 5. Validate superscript + root combination
    if parsed.get('superscript') and parsed.get('root'):
        if not is_valid_superscript_combination(parsed['superscript'], parsed['root']):
            return {
                'error_type': 'invalid_superscript_combination',
                'message': f"Invalid superscript '{parsed['superscript']}' with root '{parsed['root']}'",
                'severity': 'error',
                'component': 'superscript'
            }
    
    # 6. Validate subscripts
    # NOTE: Subscript validation temporarily disabled - incomplete rules causing false positives
    # TODO: Add comprehensive subscript combination rules
    # for subscript in parsed.get('subscripts', []):
    #     if not is_valid_subscript_combination(parsed['root'], subscript):
    #         return {
    #             'error_type': 'invalid_subscript_combination',
    #             'message': f"Invalid subscript '{subscript}' with root '{parsed['root']}'",
    #             'severity': 'error',
    #             'component': 'subscript'
    #         }
    
    # 7. Validate suffix
    if parsed.get('suffix'):
        if not is_valid_suffix(parsed['suffix']):
            return {
                'error_type': 'invalid_suffix',
                'message': f"'{parsed['suffix']}' is not a valid suffix",
                'severity': 'error',
                'component': 'suffix'
            }
    
    # 8. Validate post-suffix
    if parsed.get('post_suffix'):
        if not is_valid_post_suffix(parsed['post_suffix']):
            return {
                'error_type': 'invalid_post_suffix',
                'message': f"'{parsed['post_suffix']}' is not a valid post-suffix (only da or sa)",
                'severity': 'error',
                'component': 'post_suffix'
            }
    
    # All checks passed
    return None


def check_syllable_patterns(syllable: str) -> Optional[Dict[str, any]]:
    """
    Check syllable against pattern-based rules (length, encoding, etc.).
    
    Validates patterns for:
    - Syllables that are too long
    - Encoding errors
    - Double vowels
    - Other pattern-based issues
    
    Args:
        syllable: Tibetan syllable string
        
    Returns:
        None if valid, or error dict if invalid
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
    # Common encoding error
    if '\u0FB0' in syllable:
        return {
            'error_type': 'encoding_error',
            'message': 'Wrong "a" character (U+0FB0 instead of U+0F71)',
            'severity': 'critical',
            'component': 'encoding'
        }
    
    # Check for wrong ra (U+0F6A instead of U+0F62)
    # Common encoding error
    if '\u0F6A' in syllable:
        return {
            'error_type': 'encoding_error',
            'message': 'Wrong ra character (U+0F6A instead of U+0F62)',
            'severity': 'critical',
            'component': 'encoding'
        }
    
    # Check for double vowels (two consecutive vowel marks)
    # Invalid Tibetan pattern
    vowel_marks = [c for c in syllable if 0x0F71 <= ord(c) <= 0x0F7C]
    if len(vowel_marks) >= 2:
        # Check if they're consecutive
        for i in range(len(syllable) - 1):
            if (0x0F71 <= ord(syllable[i]) <= 0x0F7C and
                0x0F71 <= ord(syllable[i+1]) <= 0x0F7C):
                return {
                    'error_type': 'double_vowel',
                    'message': 'Double vowel marks are invalid',
                    'severity': 'error',
                    'component': 'pattern'
                }
    
    return None
