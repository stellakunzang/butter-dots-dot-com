"""
Shared definitions for achung (འ) + suffix vowel syllable endings.

Used by the syllable parser and completeness checks so allowed suffix vowels
(ི on འ for འི, ོ for འོ, …) stay in sync.
"""

# U+0F60 TIBETAN LETTER A
ACHUNG = "\u0F60"

# Vowel marks that may appear on suffix achung (after the stem).
# ི — relational འི; ོ — particle འོ (e.g. sentence-final).
ACHUNG_SUFFIX_VOWELS = frozenset(
    {
        "\u0F72",  # ི
        "\u0F7C",  # ོ
    }
)
