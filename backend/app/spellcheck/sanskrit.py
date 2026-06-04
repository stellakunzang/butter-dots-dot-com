"""
Sanskrit-transliteration detector for Tibetan text.

Sanskrit content (mantras, dharanis, proper names) is regularly written
in Tibetan script and deliberately breaks Tibetan stacking rules. Without
flagging it, every Sanskrit run looks like a wall of spelling errors.

This module scores, per syllable, the likelihood that the syllable is
Sanskrit transliteration rather than native Tibetan. Output is a float
in [0, 1].
"""
from typing import Sequence

from .data_types import TibetanSyllable
from .rules.stacking import (
    VALID_SUBSCRIPTS,
    VALID_YA_BTAGS_ROOTS,
    VALID_RA_BTAGS_ROOTS,
    VALID_LA_BTAGS_ROOTS,
    VALID_WA_ZUR_ROOTS,
)


# Codepoints that overwhelmingly appear in Sanskrit transliteration.
_SANSKRIT_MARKERS = frozenset({
    "ཾ",  # ཾ anusvara
    "ཿ",  # ཿ visarga
    "ྂ",  # ྂ candrabindu
    "ྃ",  # ྃ sign rjes su nga ro
})

# Downstream consumers (T-02b spellcheck API/UI) use this threshold to
# decide whether to annotate an error as "likely Sanskrit".
LIKELY_SANSKRIT_THRESHOLD = 0.5

# Per-signal contributions to the base score. Tuned so that a single strong
# signal lands clearly above the threshold and weaker signals stack additively.
_W_MARKER = 0.85
_W_NON_TIBETAN_SUBJOINED = 0.75
_W_THREE_STACK = 0.5
_W_INVALID_SUBSCRIPT_ROOT = 0.4

# Max additional likelihood contributed by neighbors that themselves look
# Sanskrit-like (clustering bonus). Sanskrit usually runs in contiguous
# blocks, so a neutral syllable surrounded by Sanskrit deserves a nudge.
_W_CLUSTERING_MAX = 0.3


_VALID_SUBSCRIPT_TO_ROOTS = {
    "ྱ": VALID_YA_BTAGS_ROOTS,
    "ྲ": VALID_RA_BTAGS_ROOTS,
    "ླ": VALID_LA_BTAGS_ROOTS,
    "ྭ": VALID_WA_ZUR_ROOTS,
}


def _has_sanskrit_marker(raw: str) -> bool:
    return any(ch in _SANSKRIT_MARKERS for ch in raw)


def _has_non_tibetan_subjoined(syllable: TibetanSyllable) -> bool:
    return any(sub not in VALID_SUBSCRIPTS for sub in syllable.subscripts)


def _has_three_consonant_stack(syllable: TibetanSyllable) -> bool:
    return len(syllable.subscripts) >= 2


def _has_invalid_subscript_root(syllable: TibetanSyllable) -> bool:
    root = syllable.root
    if not root:
        return False
    for sub in syllable.subscripts:
        valid_roots = _VALID_SUBSCRIPT_TO_ROOTS.get(sub)
        if valid_roots is None:
            continue
        if root not in valid_roots:
            return True
    return False


def _base_score(syllable: TibetanSyllable) -> float:
    score = 0.0
    if _has_sanskrit_marker(syllable.raw):
        score += _W_MARKER
    if _has_non_tibetan_subjoined(syllable):
        score += _W_NON_TIBETAN_SUBJOINED
    if _has_three_consonant_stack(syllable):
        score += _W_THREE_STACK
    if _has_invalid_subscript_root(syllable):
        score += _W_INVALID_SUBSCRIPT_ROOT
    return min(score, 1.0)


def score_sanskrit_likelihood(
    syllable: TibetanSyllable,
    context: Sequence[TibetanSyllable] = (),
) -> float:
    """Score the likelihood that ``syllable`` is Sanskrit transliteration.

    Args:
        syllable: The syllable to score.
        context: Neighboring syllables used for the clustering bonus.
            Callers select the window (e.g. the two syllables before
            and after the target). Pass empty for no clustering.

    Returns:
        Likelihood in [0, 1].
    """
    base = _base_score(syllable)
    if not context:
        return base

    neighbor_avg = sum(_base_score(n) for n in context) / len(context)
    return min(base + _W_CLUSTERING_MAX * neighbor_avg, 1.0)


def score_sanskrit_likelihoods(
    syllables: Sequence[TibetanSyllable],
    window: int = 2,
) -> list[float]:
    """Score a sequence of syllables, applying clustering across neighbors.

    More efficient than calling :func:`score_sanskrit_likelihood` per
    syllable since each base score is computed once.

    Args:
        syllables: Syllables in document order.
        window: Neighbors on each side considered for clustering.
    """
    bases = [_base_score(s) for s in syllables]
    scores: list[float] = []
    for i, base in enumerate(bases):
        start = max(0, i - window)
        end = min(len(bases), i + window + 1)
        neighbor_bases = [b for j, b in enumerate(bases) if start <= j < end and j != i]
        if neighbor_bases:
            bonus = _W_CLUSTERING_MAX * (sum(neighbor_bases) / len(neighbor_bases))
            scores.append(min(base + bonus, 1.0))
        else:
            scores.append(base)
    return scores
