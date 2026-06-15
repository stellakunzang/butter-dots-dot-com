# Interactive OCR — Quality Scorer Calibration (T-10)

**Date:** 2026-06-15  
**Branch:** `feat/interactive-ocr`  
**Calibration PDF:** `backend/pages_for_ocr_test.pdf` (20 pages, scanned pecha)  
**Out of scope:** Word bilingual PDFs — use copy-paste spellcheck for those.

**Related:** [INTERACTIVE_OCR_SMOKE_FINDINGS.md](INTERACTIVE_OCR_SMOKE_FINDINGS.md), [INTERACTIVE_OCR_PLAN.md](INTERACTIVE_OCR_PLAN.md) § T-10/T-11/T-13

---

## Summary

Phase-1 scorer calibration for **scanned pecha** adds hard floors (T-11 layer 1, T-13, repetition signal) and tunes composite weights/thresholds so known false accepts from the Phase A smoke run escalate instead of auto-accepting.

Re-verify command (scorer-only, no AI):

```bash
cd backend
venv/bin/python -m app.ocr_assist.run_job pages_for_ocr_test.pdf \
  --jobs-root ./jobs/calib \
  --model Woodblock \
  -v
```

---

## Chosen thresholds

| Parameter | Value | Location |
|-----------|-------|----------|
| `accept` | **0.85** | `runner.DEFAULT_THRESHOLDS` |
| `reject` | **0.50** | `runner.DEFAULT_THRESHOLDS` |
| `W_NON_TIBETAN` | 0.25 | `quality.py` |
| `W_STRUCTURAL` | 0.50 | `quality.py` |
| `W_LINE_SANITY` | 0.25 | `quality.py` |
| `W_REPETITION` | 0.20 | `quality.py` |
| `MIN_TIBETAN_SYLLABLES` | 3 | minimum-content hard floor |
| `MIXED_SCRIPT_THRESHOLD` | 0.15 | T-11 bilingual auto-accept |
| `ACHA_RUN_THRESHOLD` | 8 | ཨ spaced/stacked repetition |
| `GENERAL_CHAR_RUN_THRESHOLD` | 20 | other adjacent-char repetition |
| `MIN_LINE_COUNT_BASELINE` | 3 | pages before T-13 median is published |
| `SHORT_LINE_COUNT_RATIO` | 0.50 | hard floor when `line_count/expected` below this |

CLI overrides (unchanged from interim smoke work):

```bash
python -m app.ocr_assist.run_job book.pdf --threshold-accept 0.85 --threshold-reject 0.5 -v
```

---

## Hard floors (block auto-accept)

Applied in `quality.decide()` before composite threshold checks:

1. **Encoding errors** — any `encoding_error_count > 0` (existing).
2. **Minimum content** — fewer than 3 Tibetan syllables (TIF / ~2-char case).
3. **Stray Latin** — any `A–Z` / `a–z` on pages where `expect_mixed_script` is false (T-11 layer 1).
4. **ཨ repetition** — longest spaced/stacked ཨ run ≥ 8 on any line (page 17 failure mode).
5. **Short page vs baseline** — `line_count / expected_line_count < 0.50` once T-13 median exists (pages 19, 20).

T-11 layer 1 also computes `tibetan_only_composite_score`. When `expect_mixed_script: true` on the job baseline and `non_tibetan_char_ratio ≥ 0.15`, a page auto-accepts if the Tibetan-only composite clears `accept` (bilingual pecha — not used in this calibration PDF).

---

## T-13 line-count baseline

- Runner tracks BDRC `line_count` from accepted pages.
- After **3** accepts, publishes `expected_line_count = median(accepted line counts)` to subsequent pages.
- Persisted in each attempt's `quality.json` as `line_count`.
- On resume, seeds the baseline from finalized pages' last attempt `line_count`.

**Known limitation:** one rolling median spans the whole job. This PDF has two layout bands (~25 lines early, ~14–15 lines in the closing section). Pages at a section boundary may score lower on line sanity or escalate when the early-section median is still active (e.g. page 16 composite ~0.78). That is acceptable for scanned pecha — it surfaces borderline pages for review rather than silently accepting dropped content.

---

## Calibration sample

| Source | Pages | Human labels |
|--------|-------|--------------|
| `pages_for_ocr_test.pdf` | 20 | 4 primary false-accept fixtures + 3 stray-Latin regression pages from [INTERACTIVE_OCR_SMOKE_FINDINGS.md](INTERACTIVE_OCR_SMOKE_FINDINGS.md) |

Automated fixtures: `backend/tests/test_ocr_calibration.py` (OCR text from job `4bed0eb14c9f`).

---

## False-accept / false-reject counts (post-calibration)

Simulated sequential pass on job `a575dbe33c74` (`./jobs/calib`, Woodblock, scorer-only):

| Category | Count | Notes |
|----------|-------|-------|
| **Primary false accepts fixed** | **3 / 4** | Pages **17**, **19**, **20** now `needs_review` |
| Primary false accept remaining | **1 / 4** | Page **14** — current OCR has no Latin `S`; Devanagari/`+` mantra noise stays below hard floors. Unit test injects `S` to lock the Latin floor. |
| Stray-Latin regression (pages 2, 6, 15) | **0 false accepts** | Latin hard floor |
| Good pages (1, 4, 12 spot-check) | **0 false rejects** | Still accept at `accept=0.85` |
| Section-boundary escalate | ~1 | Page 16 may escalate when early-section median (~25) penalizes the ~15-line closing section — documented limitation |

**Target (< ~5% false accepts on human review):** 3/20 pages in the labeled failure set still auto-accept if counting page 14 only → **15%** on that narrow set; **0%** on the three structural failure modes (repetition, dropped lines, empty page). Page 14 requires OCR to emit Latin or a future T-11 layer-2 scatter detector.

---

## Before / after (Phase A vs calibrated)

| Page | Issue | Phase A | Calibrated |
|------|-------|---------|------------|
| 19 | Dropped first line | accept 0.974 | **needs_review** (short-page floor + line penalty) |
| 17 | ཨཨཨ repetition | accept 0.968 | **needs_review** (repetition floor + penalty) |
| 14 | Latin contamination | accept 0.886 | accept 0.886 *(no Latin in current OCR)* |
| 20 | Partial / 2 lines | accept 1.000 | **needs_review** (short-page floor) |
| 2, 6, 15 | Stray Latin | accept | **needs_review** (Latin floor) |

---

## Files touched

- `backend/app/ocr_assist/quality.py` — signals, hard floors, T-11 `decide` path
- `backend/app/ocr_assist/runner.py` — T-13 baseline, `ScoringContext`, quality persistence
- `backend/tests/test_ocr_calibration.py` — fixture regression tests
- `backend/tests/test_quality_scorer.py` — hard-floor unit tests
