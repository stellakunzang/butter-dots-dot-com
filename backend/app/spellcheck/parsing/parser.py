"""
Tibetan Syllable Parser

Parses a list of TypedChar into a TibetanSyllable with all components identified.

Core algorithm:
1. Scan for superscript (using stacking rules to confirm valid combination)
2. Find first vowel (vowel is always on root)
3. Identify root (from superscript rule, vowel position, or heuristic)
4. Map everything relative to root: prefix before, subscripts below, suffix after

KEY PRINCIPLE: Stacking rules are used DURING parsing, not after.
The valid combination sets are the deciding factor for structural decisions.
"""
from typing import List, Optional
from ..data_types import TypedChar, CharType, TibetanSyllable
from ..rules.stacking import (
    VALID_PREFIXES,
    VALID_SUPERSCRIPTS,
    VALID_SUFFIXES,
    VALID_POST_SUFFIXES,
    is_valid_superscript_root,
)


def parse_syllable(typed_chars: List[TypedChar]) -> TibetanSyllable:
    """
    Parse a list of typed characters into a TibetanSyllable.

    Args:
        typed_chars: Output from type_characters()

    Returns:
        TibetanSyllable with all components identified
    """
    raw = ''.join(tc.char for tc in typed_chars)

    if not typed_chars:
        return TibetanSyllable(raw=raw)

    # Step 1: Find superscript (first structural decision, informed by stacking rules)
    super_idx, root_idx = _find_superscript(typed_chars)

    # Step 2: Find first vowel
    vowel_idx = _find_first_vowel(typed_chars)

    # Step 3: Identify root and map all components
    if super_idx is not None:
        return _parse_with_superscript(typed_chars, super_idx, root_idx, vowel_idx, raw)
    elif vowel_idx is not None:
        return _parse_with_vowel(typed_chars, vowel_idx, raw)
    else:
        return _parse_no_vowel(typed_chars, raw)


# ============================================================================
# Step 1: Superscript detection
# ============================================================================

def _find_superscript(chars: List[TypedChar]) -> tuple:
    """
    Scan for a valid superscript + root pair.

    Rule: When a BASE char from {ར, ལ, ས} is immediately followed by a
    SUBJOINED char, AND the subjoined char's base form is a valid root for
    that superscript, it is a superscript+root pair.

    Being superscript-capable is necessary but NOT sufficient.
    The stacking rules are the deciding factor.

    Returns:
        (superscript_index, root_index) or (None, None)
    """
    for i in range(len(chars) - 1):
        if (chars[i].type == CharType.BASE and
                chars[i].base_form in VALID_SUPERSCRIPTS and
                chars[i + 1].type == CharType.SUBJOINED and
                is_valid_superscript_root(chars[i].base_form, chars[i + 1].base_form)):
            return (i, i + 1)
    return (None, None)


# ============================================================================
# Step 2: Vowel detection
# ============================================================================

def _find_first_vowel(chars: List[TypedChar]) -> Optional[int]:
    """Find index of first VOWEL char, or None."""
    for i, tc in enumerate(chars):
        if tc.type == CharType.VOWEL:
            return i
    return None


# ============================================================================
# Step 3a: Parse with confirmed superscript
# ============================================================================

def _parse_with_superscript(
    chars: List[TypedChar],
    super_idx: int,
    root_idx: int,
    vowel_idx: Optional[int],
    raw: str,
) -> TibetanSyllable:
    """
    Parse when we've confirmed a superscript+root pair.

    Structure: [PREFIX] + SUPERSCRIPT + ROOT + [SUBSCRIPTS] + [VOWEL] + [SUFFIX] + [POST-SUFFIX]
    """
    result = TibetanSyllable(raw=raw)
    result.superscript = chars[super_idx].base_form
    result.root = chars[root_idx].base_form  # Always base form

    # Check for prefix before superscript
    if super_idx > 0 and chars[super_idx - 1].type == CharType.BASE:
        if chars[super_idx - 1].base_form in VALID_PREFIXES:
            result.prefix = chars[super_idx - 1].base_form

    # Collect subscripts (SUBJOINED chars after root, before vowel)
    i = root_idx + 1
    while i < len(chars) and chars[i].type == CharType.SUBJOINED:
        result.subscripts.append(chars[i].char)
        i += 1

    # Collect vowel
    if i < len(chars) and chars[i].type == CharType.VOWEL:
        result.vowel = chars[i].char
        i += 1

    # Collect suffix and post-suffix
    result.suffix, result.post_suffix, i = _collect_suffixes(chars, i)

    # Anything remaining is unparsed
    result.unparsed = chars[i:]

    return result


# ============================================================================
# Step 3b: Parse with vowel (no superscript)
# ============================================================================

def _parse_with_vowel(
    chars: List[TypedChar],
    vowel_idx: int,
    raw: str,
) -> TibetanSyllable:
    """
    Parse when there's a vowel but no superscript.

    Vowel is always on the root. Work backwards from vowel to find root.
    Structure: [PREFIX] + ROOT + [SUBSCRIPTS] + VOWEL + [SUFFIX] + [POST-SUFFIX]
    """
    result = TibetanSyllable(raw=raw)

    # Find root: the last consonant (base or subjoined) before any subscripts before the vowel
    # First, collect all consonants before the vowel
    consonants_before = []
    for i in range(vowel_idx):
        if chars[i].type in (CharType.BASE, CharType.SUBJOINED):
            consonants_before.append(i)

    if not consonants_before:
        # No consonants before vowel -- unusual, just set vowel
        result.vowel = chars[vowel_idx].char
        i = vowel_idx + 1
        result.suffix, result.post_suffix, i = _collect_suffixes(chars, i)
        result.unparsed = chars[i:]
        return result

    # The root is the BASE consonant that the subscripts (if any) attach to.
    # Work backwards: skip SUBJOINED chars to find the BASE they sit below.
    root_candidate_idx = consonants_before[-1]

    # If the last consonant before vowel is SUBJOINED, find the BASE before it
    if chars[root_candidate_idx].type == CharType.SUBJOINED:
        # Find the BASE consonant these subjoined chars attach to
        base_idx = None
        for j in range(root_candidate_idx - 1, -1, -1):
            if chars[j].type == CharType.BASE:
                base_idx = j
                break

        if base_idx is not None:
            result.root = chars[base_idx].base_form
            # Everything between base and vowel that's SUBJOINED is subscripts
            for k in range(base_idx + 1, vowel_idx):
                if chars[k].type == CharType.SUBJOINED:
                    result.subscripts.append(chars[k].char)
            # Check for prefix before root
            if base_idx > 0 and chars[base_idx - 1].type == CharType.BASE:
                if chars[base_idx - 1].base_form in VALID_PREFIXES:
                    result.prefix = chars[base_idx - 1].base_form
        else:
            # All subjoined, take first as root
            result.root = chars[consonants_before[0]].base_form
            for k in range(consonants_before[0] + 1, vowel_idx):
                if chars[k].type == CharType.SUBJOINED:
                    result.subscripts.append(chars[k].char)
    else:
        # Last consonant before vowel is BASE -- that's the root
        result.root = chars[root_candidate_idx].base_form

        # Check for prefix
        if root_candidate_idx > 0 and chars[root_candidate_idx - 1].type == CharType.BASE:
            if chars[root_candidate_idx - 1].base_form in VALID_PREFIXES:
                # Need to check: is there enough structure after to justify a prefix?
                has_more = (vowel_idx < len(chars) - 1) or len(consonants_before) > 2
                if has_more or len(consonants_before) > 1:
                    result.prefix = chars[root_candidate_idx - 1].base_form

    # Collect vowel
    result.vowel = chars[vowel_idx].char
    i = vowel_idx + 1

    # Collect suffix and post-suffix
    result.suffix, result.post_suffix, i = _collect_suffixes(chars, i)

    # Anything remaining is unparsed
    result.unparsed = chars[i:]

    return result


# ============================================================================
# Step 3c: Parse without vowel
# ============================================================================

def _parse_no_vowel(
    chars: List[TypedChar],
    raw: str,
) -> TibetanSyllable:
    """
    Parse when there's no vowel mark (inherent 'a').

    Strategy: check for root+subscript patterns, then prefix, then suffix.
    """
    result = TibetanSyllable(raw=raw)

    # Single character: just the root
    if len(chars) == 1:
        if chars[0].type in (CharType.BASE, CharType.SUBJOINED):
            result.root = chars[0].base_form
        else:
            result.unparsed = list(chars)
        return result

    i = 0

    # Check if first char is BASE followed by SUBJOINED
    if (len(chars) >= 2 and
            chars[0].type == CharType.BASE and
            chars[1].type == CharType.SUBJOINED):

        # Is it root + subscript(s)?
        # (Not superscript -- that was already checked in _find_superscript)
        result.root = chars[0].base_form
        i = 1

        # Collect subscripts
        while i < len(chars) and chars[i].type == CharType.SUBJOINED:
            result.subscripts.append(chars[i].char)
            i += 1

        # Collect suffix and post-suffix
        result.suffix, result.post_suffix, i = _collect_suffixes(chars, i)
        result.unparsed = chars[i:]
        return result

    # Check for prefix
    if (chars[0].type == CharType.BASE and
            chars[0].base_form in VALID_PREFIXES and
            len(chars) >= 3):
        # Could be prefix if there's enough structure after
        # Check: prefix + BASE + SUBJOINED or prefix + BASE + BASE(suffix)
        if chars[1].type == CharType.BASE:
            if (len(chars) >= 3 and
                    (chars[2].type == CharType.SUBJOINED or
                     chars[2].type == CharType.BASE)):
                result.prefix = chars[0].base_form
                i = 1

    # After possible prefix, identify root
    if result.root is None and i < len(chars):
        if chars[i].type in (CharType.BASE, CharType.SUBJOINED):
            result.root = chars[i].base_form
            i += 1
        else:
            result.unparsed = chars[i:]
            return result

    # Collect subscripts
    while i < len(chars) and chars[i].type == CharType.SUBJOINED:
        result.subscripts.append(chars[i].char)
        i += 1

    # Collect suffix and post-suffix
    result.suffix, result.post_suffix, i = _collect_suffixes(chars, i)

    # Anything remaining is unparsed
    result.unparsed = chars[i:]

    return result


# ============================================================================
# Shared helpers
# ============================================================================

def _collect_suffixes(
    chars: List[TypedChar],
    start: int,
) -> tuple:
    """
    Collect suffix and optional post-suffix.

    Returns:
        (suffix, post_suffix, next_index)
    """
    suffix = None
    post_suffix = None
    i = start

    if i < len(chars) and chars[i].type == CharType.BASE:
        suffix = chars[i].base_form
        i += 1

        # Post-suffix: only ད or ས after a suffix
        if (i < len(chars) and
                chars[i].type == CharType.BASE and
                chars[i].base_form in VALID_POST_SUFFIXES):
            post_suffix = chars[i].base_form
            i += 1

    return (suffix, post_suffix, i)
