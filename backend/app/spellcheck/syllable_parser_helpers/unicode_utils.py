"""
Tibetan Unicode Conversion Utilities

Helper functions for converting between different Unicode forms.
"""


def subjoined_to_base(char: str) -> str:
    """
    Convert subjoined consonant to base consonant form.
    
    Subjoined consonants (U+0F90-0FBC) appear below superscripts.
    They are offset from base consonants (U+0F40-0F6C) by 0x50.
    
    Args:
        char: Subjoined consonant character
        
    Returns:
        Base consonant form (for validation)
        
    Example:
        ྒ (U+0F92, subjoined ga) → ག (U+0F42, base ga)
        ྲ (U+0FB2, subjoined ra) → ར (U+0F62, base ra)
    """
    if not char:
        return char
    
    code = ord(char)
    
    # Check if it's in subjoined range (U+0F90-0FBC)
    if 0x0F90 <= code <= 0x0FBC:
        # Convert to base form by subtracting offset
        base_code = code - 0x50
        return chr(base_code)
    
    # Already in base form or not a consonant
    return char
