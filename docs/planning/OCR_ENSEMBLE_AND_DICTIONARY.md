# OCR ensemble and dictionary-aware reading

**Status:** Ensemble measured in a spike (5 Nov 2026). Dictionary-aware reading **deferred**: no hosted database yet, and live capture / interactive OCR are local-only. Nothing here ships.
**Spike code:** `backend/spike/ensemble.py`
**Companion to:** [LIVE_PECHA_CAPTURE.md](LIVE_PECHA_CAPTURE.md), [OCR_PARITY_BASELINE.md](OCR_PARITY_BASELINE.md), [WORD_CORPUS_PLAN.md](WORD_CORPUS_PLAN.md)

---

## The idea

Woodblock, Modern and Woodblock-Stacks make different mistakes on pecha photos. Modern reads complex stacks better (སྒྲུབ, རྙིང, ལྟར). Woodblock keeps vowels and tshegs (Modern reads ནས as ནུས and drops the tsheg in དེ་ནས). Stacks is strongest on plain prose. Reading a page with all three and voting should beat any one of them.

Ume_Druma and Ume_Petsuk are out of scope. They were much worse on every leaf.

## How the spike votes

1. Run all three models on the same image. Line detection is deterministic, so the lines match.
2. Split each line into syllables, keeping their tsheg/shad.
3. Align the other two models to a pivot model (difflib over syllables).
4. Over each stretch where any model disagrees, take the reading at least two models share.
5. On a three-way split, keep the pivot's reading, or ask the dictionary (below).

Cost: three OCR passes, about 1.5 s per page warm. That fits the live capture gate.

## Results (two leaves of one pecha, hand-corrected transcriptions)

| Reading | Leaf 1 (prose) CER / syllable ER | Leaf 2 (section opening) CER / syllable ER |
| --- | --- | --- |
| Woodblock | 2.2% / 7.1% | 5.1% / 13.4% |
| Modern | 3.3% / 11.8% | 2.8% / 9.8% |
| Stacks | 1.8% / 4.7% | 7.6% / 12.5% |
| Vote, Stacks pivot, word tie-break | **0.7% / 2.4%** | 4.9% / 8.9% |
| **Vote, Modern pivot, no dictionary** | 1.2% / 3.8% | **2.8% / 8.9%** |

- The best single model changes with the page: Stacks on prose, Modern on the section opening.
- The best configuration on leaf 1 did not hold up on leaf 2. It was tuned on leaf 1.
- **Modern-pivot voting without a dictionary is the steady choice:** best or near-best on both leaves, and it needs no database.
- Two models can share a mistake and outvote the right one (leaf 2: Modern and Stacks both read དམ as དོམ).
- Two leaves of one pecha is not enough to choose a default. Re-score after the capture sitting adds more leaves.

## Dictionary-aware reading (deferred)

The corpus (`word` table: steinert 190k, monlam 107k, botok 32k entries) can break three-way splits, but only with real word handling. What the spike found:

- **Syllable lookups barely help.** Most misreads are real syllables (སྐྲབ for སྒྲུབ, སྤྲི for སྤྱི, དོམ for དམ). Only garbage like ལཏགར or ཅྱིད is caught.
- **Word lookups miss attached particles.** རྙིང་པ is in the corpus; རྙིང་པའི is not. The genitive འི, and likewise ས, ར, འང, འམ, འོ, must be split off before lookup.
- **No frequencies.** `times_seen` is 0 for every row, so a rare entry counts as much as སྒྲུབ.
- **Coverage gaps.** ལྡབ་འཕར and མགོ་ཕུར are not in the corpus.
- **No segmentation.** The spike matched greedily, left to right, two syllables either side. `app/spellcheck/dictionary.py` already defers segmentation to "Phase 3".

### What it would take

1. **Affix-aware lookup.** Split attached particles before lookup. Treat free particles (ཀྱི/གྱི/གི, ལ, ན, དུ/ཏུ/སུ, ནས, ལས, ཀྱང, དང) as words.
2. **Segmentation.** Per sentence (shad to shad), the split that covers the most syllables with dictionary words, by dynamic programming rather than greedy matching.
3. **Score candidates in context.** Substitute each model's reading into the sentence, re-segment, and prefer fewer unknown syllables and longer words.
4. **Frequencies.** Fill `times_seen` from transcribed text (the golden transcriptions, then finalized pages from interactive OCR), or take them from a source that has them (see [WORD_CORPUS_PLAN.md](WORD_CORPUS_PLAN.md)).
5. **One shared component.** The spellchecker's Phase 3 needs the same segmentation, so build it once (for example `app/spellcheck/segmentation.py`) for both the vote and spellcheck.
6. **Build or adopt.** [botok](https://github.com/OpenPecha/botok) already does affix-aware segmentation. Try it in the spike before writing our own. It is a heavy dependency with a data download.

Prerequisite: a decision on hosting and a reachable database. Until then the vote runs without a dictionary.

## What it changes for golden tests and CI

**Today.** Golden OCR fixtures (`_GOLDEN_OCR` in `test_ocr_parity.py`) pin production reads: one model (`OCR_MODEL_NAME`, Woodblock), no vote, spellcheck with the dictionary **off**. CI has no database and no ONNX models, so the golden tests skip in CI. They are a local wall.

**Known gap, already true today.** The parity tests depend on whether a database is reachable. With the local `tibetan_db` running, the dictionary turns on, `unknown_word` errors appear, and 6 existing golden tests fail even with no code change. Until that is fixed, run parity with the dictionary off:

```
cd backend && DATABASE_URL=postgresql://none@127.0.0.1:1/none pytest tests/test_ocr_parity.py
```

The fix is to pin the parity tests to dictionary-off (inject an unavailable `DictionaryService`), and later to measure golden baselines in both modes.

**If the vote ships** (local interactive OCR / live capture first):

- Golden baselines would need a second set of numbers per fixture: production (single model) and ensemble. A change to the vote must not lower the single-model wall, and the reverse.
- The vote needs all three models present locally. `scripts/download_models.py` already fetches them. The skip condition should check all three, not only `PhotiLines.onnx`.
- The spellcheck-error gap cannot see a misread that is still a valid syllable. Leaf 2 shows a gap of 3 while Woodblock gets 5.1% of characters wrong. Ensemble work should be measured by CER and syllable error rate against the transcriptions, as `spike/ensemble.py` does. A CER ceiling per golden fixture would be a stronger wall than the error gap, and it needs no dictionary.

**If the dictionary is used in the vote or spellcheck:**

- Golden fixtures would need dictionary-on baselines, measured against a pinned corpus snapshot. Otherwise a corpus import moves every number.
- CI would need a database: a Postgres service in `.github/workflows/test.yml`, seeded from a small fixed word list (the shape `scripts/seed_corpus.py` already uses), not the full 246k-row corpus.
- Dictionary-off tests should keep running, so a deployment without a database stays covered.
- Fixtures would move from local-only to CI only when CI also gets the models (cached in Actions), which [OCR_PARITY_BASELINE.md](OCR_PARITY_BASELINE.md) leaves as a later decision.

## Open questions

- Which pivot and tie-break to default to, once there are more than two leaves.
- Whether a three-model vote earns its 3× OCR cost on scans as well as photos. Not measured on the W28732 goldens.
- Whether OCRing several frames of the same page beats several models on one frame. Re-encoding one still flips 2–5 lines per leaf, so frame-to-frame variation is large (see [LIVE_PECHA_CAPTURE.md](LIVE_PECHA_CAPTURE.md)).
