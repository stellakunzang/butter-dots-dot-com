"""
Tests for the Sanskrit-transliteration detector.

Covers per-syllable scoring across native Tibetan, classic mantra
fragments, ambiguous middle-band cases, and the clustering bonus.
"""
import pytest

from app.spellcheck.data_types import TibetanSyllable
from app.spellcheck.sanskrit import (
    LIKELY_SANSKRIT_THRESHOLD,
    score_sanskrit_likelihood,
    score_sanskrit_likelihoods,
)
from app.spellcheck.syllable_parser import TibetanSyllableParser


_parser = TibetanSyllableParser()


def parse(syllable: str) -> TibetanSyllable:
    return _parser.parse_to_model(syllable)


class TestPureTibetanScoresLow:
    """Native Tibetan syllables should be well below the threshold."""

    @pytest.mark.parametrize("syllable", [
        "བཀྲ",   # prefix ba + root ka + subscript ra
        "ཀྱེ",    # ka + ya-btags + e vowel (vocative)
        "རྡོ",    # ra-mgo + da + o vowel ("stone")
        "བསམ",  # prefix ba + root sa + suffix ma ("thought")
        "དགེ",   # da-prefix + ga + e ("virtue")
    ])
    def test_below_low_band(self, syllable):
        score = score_sanskrit_likelihood(parse(syllable))
        assert score < 0.1, f"{syllable!r} scored {score}, expected < 0.1"


class TestMantraSyllablesScoreHigh:
    """Classic mantra syllables should be well above the threshold."""

    @pytest.mark.parametrize("syllable", [
        "ཨོཾ",    # om — anusvara (U+0F7E)
        "ནཿ",    # naḥ — visarga (U+0F7F)
        "ཧཱུྃ",   # huṃ — sign rjes su nga ro (U+0F83)
    ])
    def test_marker_lifts_above_high_band(self, syllable):
        score = score_sanskrit_likelihood(parse(syllable))
        assert score > 0.7, f"{syllable!r} scored {score}, expected > 0.7"


class TestNonTibetanSubjoinedScoresHigh:
    """Subjoined consonants outside the four Tibetan subscripts (ya/ra/la/wa)
    are a strong Sanskrit signal."""

    def test_subjoined_sha_ksha(self):
        # ཀྵ — ka + subjoined sha (Sanskrit kṣa conjunct)
        score = score_sanskrit_likelihood(parse("ཀྵ"))
        assert score > 0.7

    def test_subjoined_nya_jna(self):
        # ཛྙཱ — dza + subjoined nya + long-a (Sanskrit jñā)
        score = score_sanskrit_likelihood(parse("ཛྙཱ"))
        assert score > 0.7


class TestAmbiguousScoreInMiddleBand:
    """Cases that are atypical Tibetan but lack the strongest markers
    should land in a moderate band (above pure-Tibetan, below mantra)."""

    def test_three_consonant_stack(self):
        # གྲྭ — root ga + ra-btags + wa-zur (three-consonant stack, no markers)
        score = score_sanskrit_likelihood(parse("གྲྭ"))
        assert 0.3 <= score <= 0.7, f"got {score}"


class TestClusteringBonus:
    """Neutral syllables surrounded by Sanskrit-flagged neighbors should
    pick up a clustering bonus."""

    def test_neutral_syllable_lifted_by_sanskrit_context(self):
        target = parse("མ")  # neutral
        context = [parse("ཨོཾ"), parse("ཧཱུྃ"), parse("ནཿ")]

        base = score_sanskrit_likelihood(target)
        boosted = score_sanskrit_likelihood(target, context)

        assert base < 0.1
        assert boosted > base
        # Cannot exceed the clustering ceiling on a neutral target.
        assert boosted <= 0.3 + 1e-9

    def test_no_context_returns_base_score(self):
        target = parse("ཨོཾ")
        assert score_sanskrit_likelihood(target, []) == score_sanskrit_likelihood(target)

    def test_neutral_neighbors_add_no_bonus(self):
        target = parse("མ")
        context = [parse("བཀྲ"), parse("རྡོ"), parse("དགེ")]
        assert score_sanskrit_likelihood(target, context) < 0.1


class TestBatchScoring:
    """``score_sanskrit_likelihoods`` should agree with the single-syllable
    function on a flat sequence (window-based clustering)."""

    def test_batch_matches_manual_window(self):
        syllables = [
            parse("བཀྲ"),
            parse("ཨོཾ"),
            parse("ནཿ"),
            parse("མ"),
            parse("དགེ"),
        ]
        batch = score_sanskrit_likelihoods(syllables, window=2)

        # Spot-check the markered syllables sit above threshold and the
        # pure Tibetan endpoints sit below it.
        assert batch[0] < LIKELY_SANSKRIT_THRESHOLD
        assert batch[1] > LIKELY_SANSKRIT_THRESHOLD
        assert batch[2] > LIKELY_SANSKRIT_THRESHOLD
        assert all(0.0 <= s <= 1.0 for s in batch)

    def test_returns_one_score_per_syllable(self):
        syllables = [parse(s) for s in ["བཀྲ", "ཨོཾ", "མ"]]
        assert len(score_sanskrit_likelihoods(syllables)) == 3


class TestScoreRange:
    """Score must always sit within [0, 1] regardless of how many signals fire."""

    def test_stacked_signals_clip_to_one(self):
        # Construct a synthetic syllable that hits every signal.
        syllable = TibetanSyllable(
            raw="ཀྵྵཾ",
            root="ཀ",
            subscripts=["ྵ", "ྵ"],  # two non-Tibetan subjoined → three-stack + non-Tibetan
        )
        score = score_sanskrit_likelihood(syllable)
        assert 0.0 <= score <= 1.0
        assert score == 1.0  # marker + non-Tibetan + three-stack > 1.0 before clipping
