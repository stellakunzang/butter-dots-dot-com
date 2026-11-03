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
_SANSKRIT_MARKERS = frozenset(
    {
        "ཾ",  # ཾ anusvara
        "ཿ",  # ཿ visarga
        "ྂ",  # ྂ candrabindu
        "ྃ",  # ྃ sign rjes su nga ro
    }
)

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


# ---------------------------------------------------------------------------
# Text-level detection helpers.
#
# Shared by the spellcheck engine (to reclassify Sanskrit runs) and the OCR
# quality scorer (to exclude Sanskrit from the error signal), so both agree on
# what counts as Sanskrit instead of drifting apart.
# ---------------------------------------------------------------------------

_parser = None


def _get_parser():
    """Lazily build and cache the syllable parser.

    Lazy so importing this module stays cheap and dependency-light — the parser
    is only constructed when text-level detection actually runs.
    """
    global _parser
    if _parser is None:
        from .syllable_parser import TibetanSyllableParser

        _parser = TibetanSyllableParser()
    return _parser


def split_tibetan_syllables_with_position(text: str) -> list[tuple[str, int]]:
    """Split ``text`` into ``(syllable, original_position)`` pairs, Tibetan only.

    Normalizes first (same as the spellchecker) and maps each syllable's offset
    back to a position in the ORIGINAL text, so positions line up with the
    ``position`` field on spellcheck errors.
    """
    from .normalizer import is_tibetan_char, normalize_tibetan_with_position_map
    from .splitter import split_syllables_with_position

    normalized, pos_map = normalize_tibetan_with_position_map(text)
    syllables: list[tuple[str, int]] = []
    for item in split_syllables_with_position(normalized):
        syl = item["syllable"]
        if not any(is_tibetan_char(c) for c in syl):
            continue
        norm_pos = item["position"]
        mapped = pos_map[norm_pos] if norm_pos < len(pos_map) else norm_pos
        syllables.append((syl, mapped))
    return syllables


def sanskrit_syllable_positions(
    tibetan_syllables: Sequence[tuple[str, int]],
) -> tuple[set[int], set[str]]:
    """Positions and strings of the Sanskrit-likely syllables in a sequence.

    The scorer is context-sensitive (a syllable gets a clustering bonus from its
    neighbours), so the run is scored as one ordered sequence. Returns both the
    original-text positions (precise exclusion) and the syllable strings (a
    fallback for errors that carry no position).
    """
    if not tibetan_syllables:
        return set(), set()
    parser = _get_parser()
    parsed = [parser.parse_to_model(s) for s, _ in tibetan_syllables]
    likelihoods = score_sanskrit_likelihoods(parsed)
    positions: set[int] = set()
    words: set[str] = set()
    for (syl, pos), score in zip(tibetan_syllables, likelihoods):
        if score >= LIKELY_SANSKRIT_THRESHOLD:
            positions.add(pos)
            words.add(syl)
    return positions, words


def find_sanskrit_in_text(text: str) -> tuple[set[int], set[str]]:
    """Convenience: split ``text`` and return its Sanskrit-likely positions/words."""
    return sanskrit_syllable_positions(split_tibetan_syllables_with_position(text))


def error_on_sanskrit_syllable(
    error: dict,
    sanskrit_positions: set[int],
    sanskrit_words: set[str],
) -> bool:
    """Whether an error sits on a Sanskrit-likely syllable.

    Prefers a position match (so a syllable flagged Sanskrit inside a mantra
    does not suppress a genuine error on the same string elsewhere). Falls back
    to the syllable string for errors that carry no ``position`` (e.g.
    hand-crafted inputs in unit tests).
    """
    position = error.get("position")
    if position is not None:
        return position in sanskrit_positions
    return error.get("word") in sanskrit_words
