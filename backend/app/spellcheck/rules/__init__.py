"""
Tibetan Spelling Rules

Backwards compatibility layer. All data and logic has been refactored to:
- rules/stacking.py (valid combination sets and lookups)
- validation/ (validation logic)

This file re-exports everything so existing imports continue to work.
"""
from typing import Dict, Optional, Union

# Re-export all stacking rules data
from .stacking import (
    VALID_PREFIXES,
    VALID_SUPERSCRIPTS,
    VALID_SUBSCRIPTS,
    VALID_SUFFIXES,
    VALID_POST_SUFFIXES,
    VALID_WA_ZUR_ROOTS,
    VALID_YA_BTAGS_ROOTS,
    VALID_RA_BTAGS_ROOTS,
    VALID_LA_BTAGS_ROOTS,
    VALID_RA_MGO_ROOTS,
    VALID_LA_MGO_ROOTS,
    VALID_SA_MGO_ROOTS,
    VALID_GA_PREFIX_ROOTS,
    VALID_DA_PREFIX_ROOTS,
    VALID_BA_PREFIX_ROOTS,
    VALID_MA_PREFIX_ROOTS,
    VALID_ACHUNG_PREFIX_ROOTS,
)

# Re-export validation functions
from ..validation import (
    check_syllable_patterns,
    check_syllable_structure_completeness,
)


def is_valid_prefix_combination(prefix: str, root: str) -> bool:
    """Check if a prefix + root combination is valid."""
    from .stacking import is_valid_prefix_root
    return is_valid_prefix_root(prefix, root)


def is_valid_superscript_combination(superscript: str, root: str) -> bool:
    """Check if a superscript + root combination is valid."""
    from .stacking import is_valid_superscript_root
    return is_valid_superscript_root(superscript, root)


def is_valid_subscript_combination(root: str, subscript: str) -> bool:
    """Check if a root + subscript combination is valid."""
    from .stacking import is_valid_subscript_root
    return is_valid_subscript_root(root, subscript)


def is_valid_suffix(suffix: str) -> bool:
    """Check if a character is a valid suffix."""
    from .stacking import is_valid_suffix as _is_valid_suffix
    return _is_valid_suffix(suffix)


def is_valid_post_suffix(post_suffix: str) -> bool:
    """Check if a character is a valid post-suffix."""
    from .stacking import is_valid_post_suffix as _is_valid_post_suffix
    return _is_valid_post_suffix(post_suffix)


def parse_syllable_structure(syllable: str) -> Dict[str, any]:
    """
    Parse a syllable into its components.

    Uses the new pipeline (char_typer -> parser) internally.
    """
    from ..char_typing import type_characters
    from ..parsing import parse_syllable

    typed_chars = type_characters(syllable)
    model = parse_syllable(typed_chars)

    # Convert to old dict format with 'base' field for backwards compatibility
    root = model.root
    base = root  # New parser always stores root in base form

    return {
        'prefix': model.prefix,
        'superscript': model.superscript,
        'base': base,
        'root': root,
        'subscript': model.subscripts[0] if model.subscripts else None,
        'subscripts': model.subscripts,
        'vowels': [model.vowel] if model.vowel else [],
        'suffix': model.suffix,
        'post_suffix': model.post_suffix,
        'raw': model.raw,
    }


def get_error_severity(error_type: str) -> str:
    """Map error types to severity levels."""
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
    Validate a syllable structure against Tibetan spelling rules.

    Accepts either a syllable string or parsed dict for backwards compatibility.
    """
    if isinstance(syllable_or_parsed, str):
        parsed = parse_syllable_structure(syllable_or_parsed)
    else:
        parsed = syllable_or_parsed

    # Build a TibetanSyllable from the dict
    from ..data_types import TibetanSyllable
    model = TibetanSyllable(
        raw=parsed.get('raw', ''),
        prefix=parsed.get('prefix'),
        superscript=parsed.get('superscript'),
        root=parsed.get('base') or parsed.get('root'),
        subscripts=parsed.get('subscripts', []),
        vowel=parsed.get('vowels', [None])[0] if parsed.get('vowels') else None,
        suffix=parsed.get('suffix'),
        post_suffix=parsed.get('post_suffix'),
    )

    from ..validation import validate_syllable
    errors = validate_syllable(model)
    if errors:
        return errors[0].to_dict()
    return None
