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
EXCEPTED_SYLLABLES: frozenset = frozenset(
    {
        'ནའང',
        'ལའང',
    }
)

# Extremely common Sanskrit syllables (mantra cores, seed syllables, and
# loanwords) written in Tibetan script. They deliberately break Tibetan
# stacking rules but are ubiquitous and unambiguous — no reader would want them
# flagged. Allowlisting them here makes them silently valid, which also avoids
# the heuristic Sanskrit detector's false negatives on isolated forms (e.g. བཛྲ
# scores below threshold on its own). The detector in sanskrit.py still handles
# the long tail of less common Sanskrit as info-level notes.
#
# Entries are the normalized syllable string (NFC, tsheg stripped). Keep this
# list conservative: only forms that are unambiguously Sanskrit, never a valid
# Tibetan word.
COMMON_SANSKRIT: frozenset = frozenset(
    {
        'ཨོཾ',    # oṃ
        'ཨཱཿ',    # āḥ
        'ཧཱུྂ',   # hūṃ
        'བཛྲ',    # vajra
        'པདྨ',    # padma (lotus)
        'སྭཱཧཱ',  # svāhā
        'ཕཊ',     # phaṭ
    }
)


def is_excepted(syllable: str) -> bool:
    """
    Return True if this syllable bypasses normal structural validation —
    either a grammatical-convention exception or a common Sanskrit form.

    Args:
        syllable: Normalized syllable string (tsheg already stripped)
    """
    return syllable in EXCEPTED_SYLLABLES or syllable in COMMON_SANSKRIT
