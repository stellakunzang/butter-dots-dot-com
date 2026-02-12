"""
Shared Test Utilities

Common helpers used across multiple test files.
"""


def get_root_base_form(parsed_result):
    """
    Convert subjoined root to base form for test assertions.
    
    When a syllable has a superscript, the root is written in subjoined form.
    For test assertions, we often want to compare in base form.
    
    Example: སྐད has root ྐ (subjoined), base form is ཀ
    
    Args:
        parsed_result: Dictionary from TibetanSyllableParser.parse()
        
    Returns:
        Base form of root character, or None if no root
    """
    root = parsed_result.get('root')
    if not root:
        return None
    
    code = ord(root)
    if 0x0F90 <= code <= 0x0FBC:  # Subjoined form
        return chr(code - 0x50)  # Convert to base
    return root


def assert_components(parsed, **expected):
    """
    Assert multiple components match expected values.
    
    Usage:
        assert_components(parsed,
            prefix='བ',
            superscript='ར',
            root='ག',
            has_subscript='ྱ',
            vowel='ུ',
            suffix='ད'
        )
    
    Args:
        parsed: Parsed syllable dict
        **expected: Component values to check
    """
    if 'prefix' in expected:
        assert parsed.get('prefix') == expected['prefix'], \
            f"Prefix should be {expected['prefix']}, got {parsed.get('prefix')}"
    
    if 'superscript' in expected:
        assert parsed.get('superscript') == expected['superscript'], \
            f"Superscript should be {expected['superscript']}, got {parsed.get('superscript')}"
    
    if 'root' in expected:
        root = get_root_base_form(parsed)
        assert root == expected['root'], \
            f"Root should be {expected['root']}, got {root}"
    
    if 'has_subscript' in expected:
        subscripts = parsed.get('subscripts', [])
        assert expected['has_subscript'] in subscripts, \
            f"Should have subscript {expected['has_subscript']}, got {subscripts}"
    
    if 'vowel' in expected:
        vowels = parsed.get('vowels', [])
        assert expected['vowel'] in vowels, \
            f"Should have vowel {expected['vowel']}, got {vowels}"
    
    if 'suffix' in expected:
        assert parsed.get('suffix') == expected['suffix'], \
            f"Suffix should be {expected['suffix']}, got {parsed.get('suffix')}"
    
    if 'post_suffix' in expected:
        assert parsed.get('post_suffix') == expected['post_suffix'], \
            f"Post-suffix should be {expected['post_suffix']}, got {parsed.get('post_suffix')}"
