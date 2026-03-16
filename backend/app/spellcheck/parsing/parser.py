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

    # Step 0: Check for འི relational suffix pattern BEFORE normal parsing.
    #
    # འི (achung + i-vowel) can be added to syllables with no suffix or
    # suffix འ. Without this early detection, the ི vowel causes the
    # parser to misidentify འ as the root (since "root = last consonant
    # before first vowel"). Detecting this first lets us parse the body
    # correctly and attach འི as a suffix.
    achung_i_idx = _detect_achung_i_suffix(typed_chars)
    if achung_i_idx is not None:
        return _parse_with_achung_i_suffix(typed_chars, achung_i_idx, raw)

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

        # Track the earliest position we've allocated (prefix or root).
        # Anything before this that is a BASE consonant has no valid structural
        # role and must be flagged as unparsed.
        first_allocated = root_candidate_idx

        # Check for prefix
        if root_candidate_idx > 0 and chars[root_candidate_idx - 1].type == CharType.BASE:
            if chars[root_candidate_idx - 1].base_form in VALID_PREFIXES:
                # Need to check: is there enough structure after to justify a prefix?
                has_more = (vowel_idx < len(chars) - 1) or len(consonants_before) > 2
                if has_more or len(consonants_before) > 1:
                    result.prefix = chars[root_candidate_idx - 1].base_form
                    first_allocated = root_candidate_idx - 1

        # Any BASE consonants before first_allocated could not be assigned to a
        # valid syllable position. Mark them unparsed so the validator catches them.
        for j in range(first_allocated):
            if chars[j].type == CharType.BASE:
                result.unparsed.append(chars[j])

    # Collect vowel
    result.vowel = chars[vowel_idx].char
    i = vowel_idx + 1

    # Collect suffix and post-suffix
    result.suffix, result.post_suffix, i = _collect_suffixes(chars, i)

    # Anything remaining is unparsed (extend, not assign -- we may have already
    # added leading unassignable consonants above)
    result.unparsed.extend(chars[i:])

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

    # Check for prefix — 2-letter heuristic
    # Two BASE consonants where the second is NOT a valid suffix must be
    # prefix + root (root + invalid-suffix is always wrong).  This mirrors
    # the same logic in _parse_body_consonants which uses len >= 2.
    if (len(chars) == 2 and
            chars[0].type == CharType.BASE and
            chars[0].base_form in VALID_PREFIXES and
            chars[1].type == CharType.BASE and
            chars[1].base_form not in VALID_SUFFIXES):
        result.prefix = chars[0].base_form
        result.root = chars[1].base_form
        return result

    # Check for prefix — 3+ letter case
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
# Step 3d: Parse with འི relational suffix
# ============================================================================

def _detect_achung_i_suffix(chars: List[TypedChar]) -> Optional[int]:
    """
    Check if the syllable ends with འི (achung + i-vowel) relational suffix.

    This pattern must be detected BEFORE normal vowel-based parsing,
    because ི would otherwise cause འ to be misidentified as the root.

    Conditions:
    - At least 3 characters (need consonant(s) + འ + ི)
    - Last character is ི (VOWEL, U+0F72)
    - Second-to-last is འ (BASE, U+0F60)

    Returns:
        Index of འ if pattern detected, None otherwise.
    """
    n = len(chars)
    if n < 3:
        return None

    if (chars[n - 1].type == CharType.VOWEL and
            chars[n - 1].char == '\u0F72' and
            chars[n - 2].type == CharType.BASE and
            chars[n - 2].base_form == '\u0F60'):
        return n - 2

    return None


def _parse_with_achung_i_suffix(
    typed_chars: List[TypedChar],
    achung_idx: int,
    raw: str,
) -> TibetanSyllable:
    """
    Parse a syllable ending with འི relational suffix.

    Strategy:
    1. Split off the འ + ི ending
    2. Parse the body (everything before འ) to find prefix/superscript/root/subscripts/vowel
    3. If the body already has its own suffix (e.g., སྐད has suffix ད),
       the འི is NOT a valid relational -- fall back to normal parsing
    4. Otherwise, attach suffix=འ, suffix_vowel=ི

    The body should have NO suffix of its own -- the suffix is the འ from འི.
    If the body does have a suffix, the word already had a non-achung suffix
    and འི was appended incorrectly.
    """
    body = typed_chars[:achung_idx]

    result = TibetanSyllable(raw=raw)
    result.suffix = '\u0F60'   # འ
    result.suffix_vowel = '\u0F72'  # ི

    if not body:
        return result

    # Try the three parsing strategies on the body
    super_idx, root_idx = _find_superscript(body)
    vowel_idx = _find_first_vowel(body)

    if super_idx is not None:
        # Body has superscript: reuse existing logic, then copy components
        temp = _parse_with_superscript(body, super_idx, root_idx, vowel_idx, raw)

        # If the body already has a suffix (e.g., སྐད → suffix=ད),
        # the འི at the end is invalid. Fall back to normal parsing
        # so the extra འི ends up as unparsed characters.
        if temp.suffix is not None:
            return _parse_normal(typed_chars, raw)

        result.prefix = temp.prefix
        result.superscript = temp.superscript
        result.root = temp.root
        result.subscripts = temp.subscripts
        result.vowel = temp.vowel
        result.unparsed = temp.unparsed

    elif vowel_idx is not None:
        # Body has a vowel (e.g., མཐོ in མཐོའི): reuse vowel logic
        temp = _parse_with_vowel(body, vowel_idx, raw)

        # Same check: if body already has a suffix, fall back
        if temp.suffix is not None:
            return _parse_normal(typed_chars, raw)

        result.prefix = temp.prefix
        result.superscript = temp.superscript
        result.root = temp.root
        result.subscripts = temp.subscripts
        result.vowel = temp.vowel
        result.unparsed = temp.unparsed

    else:
        # Body is consonants only (e.g., ཡ, དག, བཀ)
        # Use special no-suffix logic since the suffix is འ, not in the body
        _parse_body_consonants(body, result)

    return result


def _parse_normal(
    typed_chars: List[TypedChar],
    raw: str,
) -> TibetanSyllable:
    """
    Run the normal parsing pipeline (without འི detection).

    Used as fallback when འི detection was triggered but the body
    already has its own suffix, meaning འི is not a valid relational.
    """
    super_idx, root_idx = _find_superscript(typed_chars)
    vowel_idx = _find_first_vowel(typed_chars)

    if super_idx is not None:
        return _parse_with_superscript(typed_chars, super_idx, root_idx, vowel_idx, raw)
    elif vowel_idx is not None:
        return _parse_with_vowel(typed_chars, vowel_idx, raw)
    else:
        return _parse_no_vowel(typed_chars, raw)


def _parse_body_consonants(
    body: List[TypedChar],
    result: TibetanSyllable,
) -> None:
    """
    Parse consonant-only body when suffix is known to be outside (འི pattern).

    Unlike _parse_no_vowel, this does NOT assign any body consonant as suffix,
    because the suffix is the འ from the འི ending.

    Handles:
    - Single consonant: root
    - BASE + SUBJOINED: root + subscript(s)
    - PREFIX + ROOT (+ subscripts): when first consonant is a valid prefix
    - Fallback: first consonant is root, rest is unparsed
    """
    if not body:
        return

    # Single consonant = root
    if len(body) == 1:
        if body[0].type in (CharType.BASE, CharType.SUBJOINED):
            result.root = body[0].base_form
        else:
            result.unparsed = list(body)
        return

    # Pattern: BASE + SUBJOINED = root + subscript(s)
    if (body[0].type == CharType.BASE and
            body[1].type == CharType.SUBJOINED):
        result.root = body[0].base_form
        i = 1
        while i < len(body) and body[i].type == CharType.SUBJOINED:
            result.subscripts.append(body[i].char)
            i += 1
        result.unparsed = body[i:]
        return

    # Pattern: PREFIX + ROOT (+ subscripts)
    # With no suffix in body, two BASE consonants = prefix + root
    if (body[0].type == CharType.BASE and
            body[0].base_form in VALID_PREFIXES and
            len(body) >= 2 and
            body[1].type == CharType.BASE):
        result.prefix = body[0].base_form
        result.root = body[1].base_form
        i = 2
        while i < len(body) and body[i].type == CharType.SUBJOINED:
            result.subscripts.append(body[i].char)
            i += 1
        result.unparsed = body[i:]
        return

    # Fallback: first consonant is root
    if body[0].type in (CharType.BASE, CharType.SUBJOINED):
        result.root = body[0].base_form
        i = 1
        while i < len(body) and body[i].type == CharType.SUBJOINED:
            result.subscripts.append(body[i].char)
            i += 1
        result.unparsed = body[i:]
    else:
        result.unparsed = list(body)


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
