"""
Particle Context Validation

Checks whether a particle syllable is the correct form for the suffix of
the preceding word. This is the only context-sensitive check in the
spellchecker -- all other checks operate on a single syllable in isolation.

Called from engine.check_text (not check_syllable) because it requires
knowledge of the previous syllable.
"""
from typing import Optional, Dict
from ..rules.particles import is_particle, get_particle_rule, is_valid_particle_context
from ..data_types import TibetanSyllable

# Human-readable suffix labels used in error messages
_SUFFIX_LABELS: dict = {
    'ག': 'ག (ga)',
    'ང': 'ང (nga)',
    'ད': 'ད (da)',
    'ན': 'ན (na)',
    'བ': 'བ (ba)',
    'མ': 'མ (ma)',
    'འ': 'འ (achung)',
    'ར': 'ར (ra)',
    'ལ': 'ལ (la)',
    'ས': 'ས (sa)',
    None: 'no suffix',
}

# Which particle to suggest instead, keyed by (wrong_particle, prev_suffix)
# where prev_suffix=None means no suffix.
# Rather than a large lookup, we derive the suggestion from the rules at runtime.

def _correct_form_for_suffix(category: str, suffix: Optional[str]) -> Optional[str]:
    """Return the expected particle form for this category and suffix."""
    from ..rules.particles import GENITIVE, AGENTIVE, LOCATIVE, INDEFINITE

    mapping = {
        'genitive':   GENITIVE,
        'agentive':   AGENTIVE,
        'locative':   LOCATIVE,
        'indefinite': INDEFINITE,
    }.get(category, {})

    for particle, valid in mapping.items():
        if valid is None or valid is True:
            continue
        if suffix in valid:
            return particle

    return None


def check_particle_context(
    particle_syllable: str,
    prev_parsed: TibetanSyllable,
) -> Optional[Dict]:
    """
    Check whether a particle syllable is the correct form given the preceding
    word's parsed structure.

    Returns None if valid (or if this syllable is not a tracked particle).
    Returns an error dict if the wrong particle form was used.

    Args:
        particle_syllable: Normalized syllable string (no tsheg)
        prev_parsed: Parsed structure of the immediately preceding syllable
    """
    if not is_particle(particle_syllable):
        return None

    rule = get_particle_rule(particle_syllable)
    prev_suffix = prev_parsed.suffix
    prev_post_suffix = prev_parsed.post_suffix

    if is_valid_particle_context(particle_syllable, prev_suffix, prev_post_suffix):
        return None

    # Build a helpful error message
    suffix_label = _SUFFIX_LABELS.get(prev_suffix, repr(prev_suffix))
    category = rule['category']

    suggestion = _correct_form_for_suffix(category, prev_suffix)
    suggestion_text = f" (expected {suggestion})" if suggestion else ""

    return {
        'error_type': 'wrong_particle_form',
        'message': (
            f"Wrong {category} particle '{particle_syllable}' after a word "
            f"ending in {suffix_label}{suggestion_text}"
        ),
        'severity': 'error',
        'component': 'particle',
    }
