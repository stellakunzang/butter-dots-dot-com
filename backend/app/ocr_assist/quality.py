"""
Per-page OCR quality scorer for the interactive OCR workflow.

Drives the accept/escalate/reject decision in the per-page retry loop
(see ``docs/planning/INTERACTIVE_OCR_PLAN.md`` § T-03).

Composite formula
-----------------

Each signal contributes a "badness" in [0, 1]. The composite is::

    badness = (
        W_NON_TIBETAN * non_tibetan_char_ratio
      + W_STRUCTURAL  * sanskrit_adjusted_error_ratio
      + W_LINE_SANITY * (1.0 - line_count_sanity)
      + W_PHASE2_UNKNOWN * unknown_word_ratio
    )
    composite_score = max(0.0, 1.0 - badness)

The sanskrit-adjusted error ratio is used (not the raw structural ratio)
so legitimate Sanskrit blocks — which deliberately break Tibetan stacking
rules — don't dominate the penalty.

Phase-2 (corpus lookup) input is captured as ``unknown_word_ratio`` and is
present in the composite with weight ``W_PHASE2_UNKNOWN = 0.0`` until the
word corpus is populated. The signature does not need to change when
Phase 2 is enabled — only the weight.

Encoding errors are a hard floor: any non-zero count blocks ``accept`` in
``decide`` regardless of the composite score, because a wrong-codepoint
substitution can score well structurally while being silently wrong.
"""
from dataclasses import dataclass
from typing import Literal, Sequence

from app.spellcheck.normalizer import (
    is_tibetan_char,
    normalize_tibetan_with_position_map,
)
from app.spellcheck.sanskrit import (
    LIKELY_SANSKRIT_THRESHOLD,
    score_sanskrit_likelihoods,
)
from app.spellcheck.splitter import split_syllables_with_position
from app.spellcheck.syllable_parser import TibetanSyllableParser


# Composite weights. Tuned so a clean page scores near 1.0 and a heavily
# corrupted page scores near 0. Weights are configurable here, not per-call.
W_NON_TIBETAN: float = 0.25
W_STRUCTURAL: float = 0.50
W_LINE_SANITY: float = 0.25
# TODO(phase-2): raise above 0 once the word corpus is populated.
W_PHASE2_UNKNOWN: float = 0.0


# Severity → weight multiplier for the structural error ratio numerator.
# Critical errors (encoding errors) count harder than ordinary structural
# errors; warnings (excluding Phase 2 unknown_word) count half.
_SEVERITY_WEIGHT: dict[str, float] = {
    "critical": 1.5,
    "error": 1.0,
    "warning": 0.5,
    "info": 0.0,
}

# Phase-2 errors are tracked separately, not folded into the Phase-1 ratio.
_PHASE2_ERROR_TYPES: frozenset[str] = frozenset({"unknown_word"})


@dataclass(frozen=True)
class OcrDiagnostics:
    """OCR-level signals supplied by the BDRC runner.

    ``expected_line_count`` is optional — pass ``None`` to skip the line
    sanity check (e.g. on the first page of a job where there's no baseline
    to compare against yet).
    """
    line_count: int = 0
    expected_line_count: int | None = None


@dataclass(frozen=True)
class Thresholds:
    """Decision boundaries on the composite score.

    A page with composite >= ``accept`` auto-passes. A page below ``reject``
    is too damaged to retry profitably and is queued for human review.
    Pages in between go through the AI retry loop.
    """
    accept: float
    reject: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.reject <= self.accept <= 1.0:
            raise ValueError(
                "Thresholds must satisfy 0.0 <= reject <= accept <= 1.0; "
                f"got accept={self.accept}, reject={self.reject}"
            )


@dataclass(frozen=True)
class PageQuality:
    non_tibetan_char_ratio: float
    structural_error_ratio: float
    sanskrit_adjusted_error_ratio: float
    line_count_sanity: float
    encoding_error_count: int
    unknown_word_ratio: float
    composite_score: float
    breakdown: dict[str, float]


_parser = TibetanSyllableParser()


def score_page(
    ocr_text: str,
    spellcheck_result: Sequence[dict],
    ocr_diagnostics: OcrDiagnostics,
) -> PageQuality:
    """Compute quality signals + composite for a single OCR'd page.

    ``spellcheck_result`` is the output of ``TibetanSpellChecker.check_text``;
    both Phase-1 structural errors and Phase-2 ``unknown_word`` errors may be
    present. Phase 2 entries are surfaced as ``unknown_word_ratio`` but are
    weighted at 0 in the composite for now.
    """
    tibetan_syllables = _split_tibetan_syllables(ocr_text)
    total = len(tibetan_syllables)

    # encoding_error is intentionally NOT excluded here: it is severity
    # "critical" and not a Phase-2 type, so it counts (1.5x) toward the
    # structural / sanskrit-adjusted ratio *and* separately trips the hard
    # floor in decide(). It is genuinely both a structural defect and a
    # silent-substitution risk, so the double-count is deliberate.
    structural_errors = [
        e for e in spellcheck_result
        if e.get("error_type") not in _PHASE2_ERROR_TYPES
        and e.get("severity") != "info"
    ]
    unknown_errors = [e for e in spellcheck_result if e.get("error_type") == "unknown_word"]

    structural_ratio = _ratio(_weighted_error_score(structural_errors), total)

    # The per-syllable Sanskrit parse/score is only needed to strip Sanskrit
    # errors out of the structural numerator. On a clean page (no structural
    # errors — the common case in the retry loop) there is nothing to strip,
    # so skip the work entirely.
    if structural_errors:
        sanskrit_positions, sanskrit_words = _sanskrit_syllables(tibetan_syllables)
        sanskrit_adjusted_errors = [
            e for e in structural_errors
            if not _is_sanskrit_error(e, sanskrit_positions, sanskrit_words)
        ]
    else:
        sanskrit_adjusted_errors = []
    sanskrit_adjusted_ratio = _ratio(
        _weighted_error_score(sanskrit_adjusted_errors), total
    )

    non_tibetan_ratio = _non_tibetan_char_ratio(ocr_text)
    line_sanity = _line_count_sanity(ocr_diagnostics)
    encoding_errors = sum(
        1 for e in spellcheck_result if e.get("error_type") == "encoding_error"
    )
    unknown_ratio = _ratio(len(unknown_errors), total)

    breakdown = {
        "non_tibetan_penalty": W_NON_TIBETAN * non_tibetan_ratio,
        "structural_penalty": W_STRUCTURAL * sanskrit_adjusted_ratio,
        "line_sanity_penalty": W_LINE_SANITY * (1.0 - line_sanity),
        "phase2_penalty": W_PHASE2_UNKNOWN * unknown_ratio,
    }
    composite = max(0.0, 1.0 - sum(breakdown.values()))

    return PageQuality(
        non_tibetan_char_ratio=non_tibetan_ratio,
        structural_error_ratio=structural_ratio,
        sanskrit_adjusted_error_ratio=sanskrit_adjusted_ratio,
        line_count_sanity=line_sanity,
        encoding_error_count=encoding_errors,
        unknown_word_ratio=unknown_ratio,
        composite_score=composite,
        breakdown=breakdown,
    )


def decide(
    quality: PageQuality,
    thresholds: Thresholds,
) -> Literal["accept", "escalate", "reject"]:
    """Bucket a page: auto-accept, escalate to AI retry, or queue for human."""
    if quality.encoding_error_count > 0:
        if quality.composite_score < thresholds.reject:
            return "reject"
        return "escalate"

    if quality.composite_score >= thresholds.accept:
        return "accept"
    if quality.composite_score < thresholds.reject:
        return "reject"
    return "escalate"


def _ratio(numerator: float, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return min(numerator / denominator, 1.0)


def _weighted_error_score(errors: Sequence[dict]) -> float:
    return sum(
        _SEVERITY_WEIGHT.get(e.get("severity", "error"), 1.0) for e in errors
    )


def _non_tibetan_char_ratio(text: str) -> float:
    total = sum(1 for ch in text if not ch.isspace())
    if total == 0:
        return 0.0
    non_tibetan = sum(
        1 for ch in text if not ch.isspace() and not is_tibetan_char(ch)
    )
    return non_tibetan / total


def _line_count_sanity(diagnostics: OcrDiagnostics) -> float:
    expected = diagnostics.expected_line_count
    if expected is None or expected <= 0:
        return 1.0
    deviation = abs(diagnostics.line_count - expected) / expected
    return max(0.0, 1.0 - deviation)


def _split_tibetan_syllables(text: str) -> list[tuple[str, int]]:
    """Tibetan-only syllables paired with their position in the *original* text.

    Mirrors ``TibetanSpellChecker.check_text``: normalize (NFC + zero-width
    strip) before splitting, then map each syllable's offset back to a position
    in the original text so it lines up with the ``position`` recorded on
    spellcheck errors (``engine.py:182,195``). Normalizing first also keeps the
    syllable strings byte-equal to the error ``word`` values for the fallback
    match.
    """
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


def _sanskrit_syllables(
    tibetan_syllables: Sequence[tuple[str, int]],
) -> tuple[set[int], set[str]]:
    """Positions and strings of Sanskrit-likely syllables on the page.

    The Sanskrit scorer is context-sensitive (a syllable's score gets a
    clustering bonus from its neighbours), so the page is scored as one ordered
    sequence. Returns both the set of original-text positions (for the
    position-aware exclusion) and the set of syllable strings (a fallback for
    errors that carry no position).
    """
    if not tibetan_syllables:
        return set(), set()
    syls = [s for s, _ in tibetan_syllables]
    parsed = [_parser.parse_to_model(s) for s in syls]
    likelihoods = score_sanskrit_likelihoods(parsed)
    positions: set[int] = set()
    words: set[str] = set()
    for (syl, pos), score in zip(tibetan_syllables, likelihoods):
        if score >= LIKELY_SANSKRIT_THRESHOLD:
            positions.add(pos)
            words.add(syl)
    return positions, words


def _is_sanskrit_error(
    error: dict,
    sanskrit_positions: set[int],
    sanskrit_words: set[str],
) -> bool:
    """Whether a structural error sits on a Sanskrit-likely syllable.

    Prefers a position match (precise — a syllable flagged Sanskrit inside a
    mantra no longer suppresses a genuine error on the same string elsewhere).
    Falls back to string match for errors that carry no ``position`` (e.g.
    hand-crafted inputs in unit tests).
    """
    position = error.get("position")
    if position is not None:
        return position in sanskrit_positions
    return error.get("word") in sanskrit_words
