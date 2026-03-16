"""
Excepted syllables

Syllables that are valid by grammatical convention but fail structural
validation rules. These are checked before the normal validation pipeline
and returned as valid (no error) when matched.

Each entry is the normalized syllable string (no tsheg), with a comment
explaining why it's excepted.
"""

# Compound particles formed by joining a locative particle with འང་ ("even/also").
# The ང after suffix འ looks like an invalid post-suffix (only ད and ས are valid),
# but these forms are grammatically established and appear throughout classical texts.
#
#   ནའང་ = ན་ (locative "in/at") + འང་ → "even in/at"
#   ལའང་ = ལ་ (locative "to/at")  + འང་ → "even to/at"
EXCEPTED_SYLLABLES: frozenset = frozenset({
    'ནའང',
    'ལའང',
})


def is_excepted(syllable: str) -> bool:
    """
    Return True if this syllable is in the exception list and should
    bypass normal structural validation.

    Args:
        syllable: Normalized syllable string (tsheg already stripped)
    """
    return syllable in EXCEPTED_SYLLABLES
