"""
Tibetan Particle Rules

Which particle form is correct depends on the suffix of the preceding word.
This module defines that mapping as pure data.

Representation:
  - frozenset({...}): particle is valid only when the preceding word's suffix
    is in this set. Use None in the set to mean "no suffix" (word ends with
    just its root consonant or vowel, no suffix letter).
  - True: particle is unrestricted -- valid after any preceding word.
  - None: lenient variant -- skip context checking entirely.

References: edge_cases.md particle rules section.
"""
from typing import Optional, FrozenSet, Union

# Sentinel used in valid-suffix sets to mean "preceding word has no suffix"
NO_SUFFIX = None


# ============================================================================
# Particle → valid preceding suffixes
# ============================================================================

# Genitive (bdag gi sgra)
GENITIVE: dict = {
    'ཀྱི': frozenset({'ད', 'བ', 'ས'}),
    'གི':  frozenset({'ག', 'ང'}),
    'གྱི': frozenset({'ན', 'མ', 'ར', 'ལ'}),
    'འི':  frozenset({'འ', NO_SUFFIX}),
    'ཡི':  None,   # lenient variant of འི -- always accepted
}

# Agentive (byed pa'i sgra)
AGENTIVE: dict = {
    'ཀྱིས': frozenset({'ད', 'བ', 'ས'}),
    'གིས':  frozenset({'ག', 'ང'}),
    'གྱིས': frozenset({'ན', 'མ', 'ར', 'ལ'}),
    'ས':    frozenset({'འ', NO_SUFFIX}),
    'ཡིས':  None,  # lenient variant of ས -- always accepted
}

# Locative (gnas gzhi'i sgra)
# ན and ལ are unrestricted (True); the rest have specific suffix requirements.
LOCATIVE: dict = {
    'ན':  True,
    'ལ':  True,
    'སུ': frozenset({'ས'}),
    'ཏུ': frozenset({'ག', 'བ'}),   # also valid after post-suffix ད (handled separately)
    'ར':  frozenset({'འ'}),
    'རུ': frozenset({'འ', NO_SUFFIX}),
    'དུ': frozenset({'ང', 'ད', 'ན', 'མ', 'ར', 'ལ'}),
}

# Indefinite article (sgra med kyi sgra)
# ཞིག is the default form used after everything not covered by ཅིག or ཤིག.
# We represent this as all valid suffixes minus {ག,ད,བ,ས}.
_INDEF_ZHIG_VALID = frozenset({'ང', 'ན', 'མ', 'འ', 'ར', 'ལ', NO_SUFFIX})

INDEFINITE: dict = {
    'ཅིག': frozenset({'ག', 'ད', 'བ'}),
    'ཤིག': frozenset({'ས'}),
    'ཞིག': _INDEF_ZHIG_VALID,
}

# Combined lookup: particle string → (category label, valid suffixes or sentinel)
PARTICLE_RULES: dict = {}
for _category, _rules in [
    ('genitive',   GENITIVE),
    ('agentive',   AGENTIVE),
    ('locative',   LOCATIVE),
    ('indefinite', INDEFINITE),
]:
    for _particle, _valid in _rules.items():
        PARTICLE_RULES[_particle] = {
            'category': _category,
            'valid_suffixes': _valid,  # frozenset | True | None
        }


def is_particle(syllable: str) -> bool:
    """Return True if this syllable is a known particle form."""
    return syllable in PARTICLE_RULES


def get_particle_rule(syllable: str) -> Optional[dict]:
    """
    Return the rule dict for this particle, or None if not a particle.

    The returned dict has keys:
        category (str): 'genitive' | 'agentive' | 'locative' | 'indefinite'
        valid_suffixes: frozenset | True | None
    """
    return PARTICLE_RULES.get(syllable)


def is_valid_particle_context(
    particle: str,
    prev_suffix: Optional[str],
    prev_post_suffix: Optional[str] = None,
) -> bool:
    """
    Check whether this particle is the correct form for the preceding word.

    Args:
        particle: The particle syllable string (normalized, no tsheg)
        prev_suffix: The suffix letter of the preceding word, or None if none
        prev_post_suffix: The post-suffix of the preceding word, or None

    Returns:
        True if the particle is valid in this context, False if it is wrong
    """
    rule = PARTICLE_RULES.get(particle)
    if rule is None:
        return True   # Not a particle we track -- no opinion

    valid = rule['valid_suffixes']

    if valid is None:
        return True   # Lenient variant -- always valid

    if valid is True:
        return True   # Unrestricted particle -- always valid

    # Special case: ཏུ is also valid after post-suffix ད
    if particle == 'ཏུ' and prev_post_suffix == 'ད':
        return True

    return prev_suffix in valid
