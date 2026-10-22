"""
Tibetan Stacking Rules

Which letters can stack together in which positions within a syllable.
This is pure data and lookup functions -- no parsing or validation logic.

Based on traditional Tibetan stacking rules and the authoritative
valid stacks list (see /docs/research/VALID_STACKS_REFERENCE.md).
"""


# ============================================================================
# Valid component sets
# ============================================================================

# The 5 valid prefixes (sngon-'jug)
VALID_PREFIXES = {'ག', 'ད', 'བ', 'མ', 'འ'}  # ga, da, ba, ma, achung

# The 3 valid superscripts
VALID_SUPERSCRIPTS = {'ར', 'ལ', 'ས'}  # ra-mgo, la-mgo, sa-mgo

# The 4 valid subscripts (in subjoined form)
VALID_SUBSCRIPTS = {'\u0fb1', '\u0fb2', '\u0fb3', '\u0fad'}  # ya, ra, la, wa

# The 10 valid suffixes
VALID_SUFFIXES = {'ག', 'ང', 'ད', 'ན', 'བ', 'མ', 'འ', 'ར', 'ལ', 'ས'}

# The 2 valid post-suffixes
VALID_POST_SUFFIXES = {'ད', 'ས'}  # da, sa


# ============================================================================
# Superscript + root combinations
# Which roots can each superscript sit above?
# ============================================================================

VALID_RA_MGO_ROOTS = {'ཀ', 'ག', 'ང', 'ཇ', 'ཉ', 'ཏ', 'ད', 'ན', 'བ', 'མ', 'ཙ', 'ཛ'}

VALID_LA_MGO_ROOTS = {'ཀ', 'ག', 'ང', 'ཅ', 'ཇ', 'ཏ', 'ད', 'པ', 'བ', 'ཧ'}

VALID_SA_MGO_ROOTS = {'ཀ', 'ག', 'ང', 'ཉ', 'ཏ', 'ད', 'ན', 'པ', 'བ', 'མ', 'ཙ'}

# Map superscript letter -> set of valid roots beneath it
_SUPERSCRIPT_ROOT_MAP = {
    'ར': VALID_RA_MGO_ROOTS,
    'ལ': VALID_LA_MGO_ROOTS,
    'ས': VALID_SA_MGO_ROOTS,
}


# ============================================================================
# Subscript + root combinations
# Which roots can each subscript sit below?
# ============================================================================

VALID_YA_BTAGS_ROOTS = {'ཀ', 'ཁ', 'ག', 'པ', 'ཕ', 'བ', 'མ'}

VALID_RA_BTAGS_ROOTS = {'ཀ', 'ཁ', 'ག', 'ཏ', 'ཐ', 'ད', 'པ', 'ཕ', 'བ', 'མ', 'ཤ', 'ས', 'ཧ'}

VALID_LA_BTAGS_ROOTS = {'ཀ', 'ག', 'བ', 'ཟ', 'ར', 'ས'}

VALID_WA_ZUR_ROOTS = {'ཀ', 'ཁ', 'ག', 'ཅ', 'ཉ', 'ཏ', 'ད', 'ཙ', 'ཚ', 'ཞ', 'ཟ', 'ར', 'ཤ', 'ས', 'ཧ'}

# Map subscript letter (subjoined form) -> set of valid roots above it
_SUBSCRIPT_ROOT_MAP = {
    '\u0fb1': VALID_YA_BTAGS_ROOTS,  # ya-btags
    '\u0fb2': VALID_RA_BTAGS_ROOTS,  # ra-btags
    '\u0fb3': VALID_LA_BTAGS_ROOTS,  # la-btags
    '\u0fad': VALID_WA_ZUR_ROOTS,  # wa-zur
}


# ============================================================================
# Valid prefix + root combinations
# Which roots can each prefix precede?
#
# Derived from VBA source (Tibetan_Spellchecker_vba.txt line 334) by
# inverting the invalid list. Uses positive validation for consistency
# with superscript/subscript rules and to avoid the character-name
# errors that plagued the negative (INVALID_PREFIX_COMBOS) approach.
# ============================================================================

VALID_GA_PREFIX_ROOTS = {
    # Attested: གཅིག gcig, གཉིས gnyis, གཏོང gtong, གདན gdan,
    #   གནས gnas, གཙོ gtso, གཞི gzhi, གཟུགས gzugs,
    #   གཡུ g.yu, གཤེགས gshegs, གསོལ gsol, གང gang
    'ག',
    'ང',
    'ཅ',
    'ཉ',
    'ཏ',
    'ད',
    'ན',
    'བ',
    'མ',
    'ཙ',
    'ཞ',
    'ཟ',
    'འ',
    'ཡ',
    'ར',
    'ལ',
    'ཤ',
    'ས',
    'ཨ',
}

VALID_DA_PREFIX_ROOTS = {
    # Attested: དཀར dkar, དགའ dga', དངོས dngos, དངུལ dngul,
    #   དཔལ dpal, དབང dbang, དམག dmag
    'ཀ',
    'ག',
    'ང',
    'ད',
    'ན',
    'པ',
    'བ',
    'མ',
    'འ',
    'ར',
    'ལ',
    'ས',
    'ཨ',
}

VALID_BA_PREFIX_ROOTS = {
    # Attested: བཀའ bka', བགྲོ bgro, བཅོས bcos, བཏང btang,
    #   བདེ bde, བསམ bsam, བཞི bzhi
    'ཀ',
    'ག',
    'ང',
    'ཅ',
    'ཏ',
    'ད',
    'ན',
    'བ',
    'མ',
    'ཙ',
    'ཞ',
    'ཟ',
    'འ',
    'ར',
    'ལ',
    'ཤ',
    'ས',
    'ཨ',
}

VALID_MA_PREFIX_ROOTS = {
    # Attested: མཁའ mkha', མགོ mgo, མཆོད mchod, མཇལ mjal,
    #   མཉམ mnyam, མཐོ mtho, མདུན mdun, མནའ mna'
    'ཁ',
    'ག',
    'ང',
    'ཆ',
    'ཇ',
    'ཉ',
    'ཐ',
    'ད',
    'ན',
    'བ',
    'མ',
    'ཚ',
    'ཛ',
    'འ',
    'ར',
    'ལ',
    'ས',
    'ཨ',
}

VALID_ACHUNG_PREFIX_ROOTS = {
    # Attested: འགྲོ 'gro, འཇིག 'jig, འདིར 'dir, འབྲས 'bras,
    #   འཛིན 'dzin, འཕགས 'phags
    'ཁ',
    'ག',
    'ང',
    'ཆ',
    'ཇ',
    'ཐ',
    'ད',
    'ན',
    'ཕ',
    'བ',
    'མ',
    'ཚ',
    'ཛ',
    'འ',
    'ར',
    'ལ',
    'ས',
    'ཨ',
}

# Map prefix letter -> set of valid roots after it
_PREFIX_ROOT_MAP = {
    'ག': VALID_GA_PREFIX_ROOTS,
    'ད': VALID_DA_PREFIX_ROOTS,
    'བ': VALID_BA_PREFIX_ROOTS,
    'མ': VALID_MA_PREFIX_ROOTS,
    'འ': VALID_ACHUNG_PREFIX_ROOTS,
}


# ============================================================================
# Lookup functions
# ============================================================================


def _to_base(char: str) -> str:
    """Convert subjoined form to base form if needed."""
    code = ord(char)
    if 0x0F90 <= code <= 0x0FBC:
        return chr(code - 0x50)
    return char


def is_valid_superscript_root(superscript: str, root: str) -> bool:
    """
    Can this superscript sit above this root?

    Both the superscript identity AND the root must be valid for the
    combination to be a real superscript+root stack. This is the deciding
    factor for distinguishing superscript+root from root+subscript.

    Example:
        is_valid_superscript_root('ས', 'ཀ') -> True  (sa-mgo over ka)
        is_valid_superscript_root('ས', 'ར') -> False (sa cannot sit over ra)

    Args:
        superscript: The potential superscript (base form)
        root: The potential root (base or subjoined form)
    """
    if superscript not in _SUPERSCRIPT_ROOT_MAP:
        return False
    return _to_base(root) in _SUPERSCRIPT_ROOT_MAP[superscript]


def is_valid_subscript_root(root: str, subscript: str) -> bool:
    """
    Can this subscript sit below this root?

    Args:
        root: The root (base or subjoined form)
        subscript: The subscript (subjoined form)
    """
    if subscript not in _SUBSCRIPT_ROOT_MAP:
        return False
    return _to_base(root) in _SUBSCRIPT_ROOT_MAP[subscript]


def is_valid_prefix_root(prefix: str, root: str) -> bool:
    """
    Can this prefix precede this root?

    Uses positive validation: the combination must be in the valid set.
    Consistent with superscript/subscript validation approach.

    Args:
        prefix: The prefix character (base form)
        root: The root character (base or subjoined form)
    """
    if not prefix or not root:
        return False
    if prefix not in _PREFIX_ROOT_MAP:
        return False
    return _to_base(root) in _PREFIX_ROOT_MAP[prefix]


def is_valid_suffix(char: str) -> bool:
    """Is this character a valid suffix?"""
    return char in VALID_SUFFIXES


def is_valid_post_suffix(char: str) -> bool:
    """Is this character a valid post-suffix (ད or ས)?"""
    return char in VALID_POST_SUFFIXES
