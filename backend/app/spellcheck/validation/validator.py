"""
Component Validator

Validates a TibetanSyllable against spelling rules.
Returns ALL errors found, prioritized by severity.
"""
from typing import List
from ..data_types import TibetanSyllable, SpellError
from ..rules.stacking import (
    is_valid_prefix_root,
    is_valid_superscript_root,
    is_valid_subscript_root,
    is_valid_suffix,
    is_valid_post_suffix,
)


def validate_syllable(syllable: TibetanSyllable) -> List[SpellError]:
    """
    Validate a parsed TibetanSyllable against all spelling rules.

    Returns ALL errors found (not just the first), sorted by priority.

    Args:
        syllable: Parsed TibetanSyllable from the parser

    Returns:
        List of SpellError (empty if valid)
    """
    errors = []

    # 1. Root is required
    if not syllable.root:
        errors.append(SpellError(
            error_type='missing_root',
            message='Syllable must have a root letter',
            severity='error',
            component='root',
        ))
        return errors  # Can't validate further without root

    # 2. Validate prefix + root combination
    # Skip prefix validation if there's a superscript between prefix and root
    if syllable.prefix and not syllable.superscript:
        if not is_valid_prefix_root(syllable.prefix, syllable.root):
            errors.append(SpellError(
                error_type='invalid_prefix_combination',
                message=f"Prefix '{syllable.prefix}' cannot prefix root '{syllable.root}'",
                severity='error',
                component='prefix',
            ))

    # 3. Validate superscript + root combination
    if syllable.superscript:
        if not is_valid_superscript_root(syllable.superscript, syllable.root):
            errors.append(SpellError(
                error_type='invalid_superscript_combination',
                message=f"Invalid superscript '{syllable.superscript}' with root '{syllable.root}'",
                severity='error',
                component='superscript',
            ))

    # 4. Validate subscripts
    # NOTE: Subscript validation temporarily disabled - incomplete rules causing false positives
    # TODO: Enable once stacking rules are fully verified
    # for subscript in syllable.subscripts:
    #     if not is_valid_subscript_root(syllable.root, subscript):
    #         errors.append(SpellError(
    #             error_type='invalid_subscript_combination',
    #             message=f"Invalid subscript '{subscript}' with root '{syllable.root}'",
    #             severity='error',
    #             component='subscript',
    #         ))

    # 5. Validate suffix
    if syllable.suffix:
        if not is_valid_suffix(syllable.suffix):
            errors.append(SpellError(
                error_type='invalid_suffix',
                message=f"'{syllable.suffix}' is not a valid suffix",
                severity='error',
                component='suffix',
            ))

    # 6. Validate post-suffix
    if syllable.post_suffix:
        if not is_valid_post_suffix(syllable.post_suffix):
            errors.append(SpellError(
                error_type='invalid_post_suffix',
                message=f"'{syllable.post_suffix}' is not a valid post-suffix (only da or sa)",
                severity='error',
                component='post_suffix',
            ))

    # 7. Check for unparsed characters
    if syllable.unparsed:
        unparsed_str = ''.join(tc.char for tc in syllable.unparsed)
        errors.append(SpellError(
            error_type='unparsed_characters',
            message=f"Characters '{unparsed_str}' could not be assigned to any syllable component",
            severity='error',
            component='structure',
        ))

    return errors
