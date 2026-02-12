"""
Tibetan Unicode Normalization and Character Validation

Handles Unicode normalization (NFC), zero-width character removal,
and Tibetan character validation.
"""
import unicodedata
from typing import Optional, List, Dict


def normalize_tibetan(text: str) -> str:
    """
    Normalize Tibetan text to NFC form and remove zero-width characters.
    
    Args:
        text: Tibetan text to normalize
        
    Returns:
        Normalized text in NFC form with zero-width characters removed
    """
    # Normalize to NFC (composed) form
    text = unicodedata.normalize('NFC', text)
    
    # Remove zero-width characters
    text = text.replace('\u200b', '')  # Zero-width space
    text = text.replace('\u200c', '')  # Zero-width non-joiner
    text = text.replace('\u200d', '')  # Zero-width joiner
    
    return text


def is_tibetan_char(char: str) -> bool:
    """
    Check if a character is in the Tibetan Unicode range.
    
    Tibetan Unicode range: U+0F00 to U+0FFF
    
    Args:
        char: Single character to check
        
    Returns:
        True if character is Tibetan, False otherwise
    """
    if not char or len(char) == 0:
        return False
    
    code = ord(char[0])
    
    # Tibetan Unicode range: 0x0F00 - 0x0FFF
    return 0x0F00 <= code <= 0x0FFF


def extract_tibetan(text: str) -> str:
    """
    Extract only Tibetan characters from mixed text.
    
    Preserves Tibetan letters, vowels, punctuation (tsheg, shad).
    Removes non-Tibetan characters (Latin, numbers, etc.).
    
    Args:
        text: Mixed script text
        
    Returns:
        Text containing only Tibetan characters
    """
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
        # Skip whitespace - it's normal and expected
        if char.isspace():
            continue
        
        # Count non-Tibetan characters
        if not is_tibetan_char(char):
            non_tibetan_count += 1
    
    return {
        'count': non_tibetan_count,
        'has_non_tibetan': non_tibetan_count > 0
    }
