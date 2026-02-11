"""
Validation stage of the spellcheck pipeline.

Three levels of validation:
1. Pattern checks (raw string) -- encoding errors, unusual marks
2. Structural completeness (raw string vs parsed) -- unparsed characters
3. Component validation (parsed structure) -- invalid combinations

Re-exports:
    validate_syllable: Validate a parsed TibetanSyllable
    check_syllable_patterns: Check raw string for pattern issues
    check_syllable_structure_completeness: Check parsed vs raw completeness
"""
from .validator import validate_syllable
from .pattern_checks import check_syllable_patterns
from .completeness_checks import check_syllable_structure_completeness

__all__ = [
    'validate_syllable',
    'check_syllable_patterns',
    'check_syllable_structure_completeness',
]
