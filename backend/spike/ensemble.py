"""Throwaway: read a still with Woodblock, Modern and Woodblock-Stacks, vote per syllable (issue #79).

    cd backend && venv/bin/python -m spike.ensemble spike/stills/leaf-1.jpg [--truth spike/transcripts/leaf-1.txt]

Woodblock is the pivot. Modern and Stacks are aligned to it syllable by syllable
(difflib on tsheg/shad tokens); over each stretch where any model disagrees, the majority reading wins.
A three-way split goes to whichever reading the dictionary knows, else Woodblock.
With --truth, prints character and syllable error rates for every model and the vote.
Truth files may carry '#' note lines; they are ignored.
"""

from __future__ import annotations

import argparse
import difflib
import re
from collections import Counter
from pathlib import Path

import cv2

from app.pdf.ocr import get_engine

MODELS = ("Woodblock", "Modern", "Woodblock-Stacks")
PIVOT = "Woodblock"
_TOKEN = re.compile(r"[^་།༎༔ཿ\s]+[་།༎༔ཿ\s]*|[་།༎༔ཿ\s]+")


def tokens(line: str) -> list[str]:
    """Syllables with their trailing tsheg/shad attached, so punctuation votes too."""
    return _TOKEN.findall(line)


class Alignment:
    """Maps pivot token boundaries to positions in another model's tokens."""

    def __init__(self, pivot: list[str], other: list[str]):
        self.other = other
        n = len(pivot)
        self.lo = [len(other)] * (n + 1)
        self.hi = [0] * (n + 1)
        self.diff_spans: list[tuple[int, int]] = []
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, pivot, other, autojunk=False).get_opcodes():
            if tag == "equal":
                for k in range(i1, i2 + 1):
                    self._mark(k, j1 + k - i1)
            else:
                self._mark(i1, j1)
                self._mark(i2, j2)
                self.diff_spans.append((i1, i2))

    def _mark(self, k: int, j: int) -> None:
        self.lo[k] = min(self.lo[k], j)
        self.hi[k] = max(self.hi[k], j)

    def reading(self, start: int, end: int) -> str:
        """What this model reads over pivot tokens [start, end), insertions included."""
        return "".join(self.other[self.lo[start]:self.hi[end]])


def _regions(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge overlapping or touching disagreement spans (zero-width = insertion)."""
    merged: list[list[int]] = []
    for s, e in sorted(spans):
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return [(s, e) for s, e in merged]


_SPLIT = re.compile(r"[་།༎༔ཿ\s]+")


def _syllables(text: str) -> list[str]:
    return [x for x in _SPLIT.split(text) if x]


class Lexicon:
    """Syllable inventory and multi-syllable words from the spellcheck corpus."""

    MAX_WORD = 4

    def __init__(self):
        from sqlalchemy import text
        from app.database import db_available, get_session
        from app.spellcheck.dictionary import _normalize

        self.syllables: set[str] = set()
        self.words: set[tuple[str, ...]] = set()
        if not db_available():
            return
        with get_session() as session:
            rows = session.execute(text("SELECT word_normalized FROM word")).fetchall()
        for (word,) in rows:
            parts = tuple(_syllables(_normalize(word)))
            self.syllables.update(parts)
            if 2 <= len(parts) <= self.MAX_WORD:
                self.words.add(parts)

    def __bool__(self) -> bool:
        return bool(self.syllables)

    def known_syllables(self, syls: list[str]) -> int:
        return sum(s in self.syllables for s in syls)

    def word_cover(self, syls: list[str]) -> int:
        """Syllables covered by multi-syllable dictionary words (greedy longest match)."""
        covered, i = 0, 0
        while i < len(syls):
            for n in range(min(self.MAX_WORD, len(syls) - i), 1, -1):
                if tuple(syls[i:i + n]) in self.words:
                    covered += n
                    i += n
                    break
            else:
                i += 1
        return covered


def make_scorer(mode: str, lexicon: Lexicon | None):
    """Tie-break score for a candidate reading given 2 tokens of context each side."""
    if mode == "none" or not lexicon:
        return None
    if mode == "syllable":
        return lambda cand, left, right: lexicon.known_syllables(_syllables(cand)) - len(_syllables(cand)) * 0.0
    if mode == "word":
        def score(cand, left, right):
            window = _syllables(left) + _syllables(cand) + _syllables(right)
            return lexicon.word_cover(window) + 0.5 * lexicon.known_syllables(_syllables(cand))
        return score
    raise ValueError(mode)


def vote_line(reads: dict[str, str], scorer=None, pivot_model: str = PIVOT) -> tuple[str, int]:
    """Vote over each stretch where any model disagrees with the pivot."""
    pivot = tokens(reads[pivot_model])
    aligned = [Alignment(pivot, tokens(reads[m])) for m in MODELS if m != pivot_model]
    regions = _regions([span for a in aligned for span in a.diff_spans])
    voted, overrides, cursor = [], 0, 0
    for start, end in regions:
        voted.extend(pivot[cursor:start])
        base = "".join(pivot[start:end])
        options = [base] + [a.reading(start, end) for a in aligned]
        top, count = Counter(options).most_common(1)[0]
        if count == 1 and scorer is not None:
            left, right = "".join(pivot[max(0, start - 2):start]), "".join(pivot[end:end + 2])
            best = max(scorer(o, left, right) for o in options)
            top = next(o for o in options if scorer(o, left, right) == best)
        elif count == 1:
            top = base
        overrides += top != base
        voted.append(top)
        cursor = end
    voted.extend(pivot[cursor:])
    return "".join(voted), overrides


def read_all(image) -> dict[str, list[str]]:
    engine = get_engine()
    return {
        m: [l.text for l in engine.run_on_image(image, page_settings={"model_variant": m})]
        for m in MODELS
    }


def _lev(a, b) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def score(lines: list[str], truth: list[str]) -> tuple[float, float]:
    hyp, ref = "".join("".join(lines).split()), "".join("".join(truth).split())
    cer = _lev(hyp, ref) / max(len(ref), 1)
    hs = [s for s in re.split(r"[་།༎༔ཿ]+", hyp) if s]
    rs = [s for s in re.split(r"[་།༎༔ཿ]+", ref) if s]
    return cer, _lev(hs, rs) / max(len(rs), 1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument("--truth")
    args = parser.parse_args()

    lexicon = Lexicon()
    print(f"dictionary: {len(lexicon.syllables)} syllables, {len(lexicon.words)} multi-syllable words")
    reads = read_all(cv2.imread(args.image))
    n = min(len(v) for v in reads.values())

    results = {m: reads[m] for m in MODELS}
    for pivot_model in MODELS:
        for mode in ("none", "syllable", "word"):
            scorer = make_scorer(mode, lexicon)
            lines = [vote_line({m: reads[m][i] for m in MODELS}, scorer, pivot_model)[0] for i in range(n)]
            results[f"vote {pivot_model}/{mode}"] = lines

    if not args.truth:
        for name, lines in results.items():
            print(f"== {name}"); print("\n".join(lines))
        return
    truth = [l for l in Path(args.truth).read_text().splitlines() if l.strip() and not l.startswith("#")]
    print(f"\n{'reading':28} {'CER':>6} {'syl ER':>7}")
    for name, lines in results.items():
        cer, ser = score(lines, truth)
        print(f"{name:28} {cer:6.3f} {ser:7.3f}")


if __name__ == "__main__":
    main()
