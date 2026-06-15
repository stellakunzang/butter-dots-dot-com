# Interactive OCR — Smoke Test Findings (Phase A)

**Companion to:** [INTERACTIVE_OCR_LOCAL_SMOKE.md](INTERACTIVE_OCR_LOCAL_SMOKE.md), [INTERACTIVE_OCR_PLAN.md](INTERACTIVE_OCR_PLAN.md)  
**Purpose:** Human-labeled pages from the first Phase A run — input for **T-10** (threshold calibration), **T-11** (mixed-script / contamination guardrails), and **T-13** (line-count sanity baseline).

**Status:** Phase A complete on sample PDF; Phase B+ not yet run on these labels.

---

## Run metadata

| Field | Value |
|-------|--------|
| Job ID | `4bed0eb14c9f` |
| Source PDF | `backend/pages_for_ocr_test.pdf` (20 pages) |
| Branch | `feat/interactive-ocr` |
| CLI | BDRC-only (no `--enable-ai`) |
| Model | `Woodblock` |
| Default thresholds | `accept=0.9`, `reject=0.5` (raised from 0.85 interim for smoke — revert/tune in T-10) |
| Job dir | `backend/jobs/4bed0eb14c9f/` |

---

## Executive summary

Phase A auto-accepted pages that a human would reject. Three root causes in the current scorer:

1. **`non_tibetan_char_ratio` is proportional, not presence-based.** A single Latin letter (or a few Devanagari/`+` glyphs) on a long page contributes a negligible penalty and stays above `accept=0.85`. Spellcheck emits `non_tibetan_skipped` at **info** severity — it does not affect the structural ratio or block accept.

2. **`line_count_sanity` is inert.** `expected_line_count` is never set in the runner, so `line_count_sanity` is always `1.0` and the line-sanity weight contributes nothing. See **T-13**.

3. **Repeated-`ཨ` garbage is under-penalized structurally.** Page 17’s run of stacked `ཨ` syllables scores composite **0.97** — well above accept — even though this pattern is a known BDRC failure mode for this corpus.

4. **No minimum-content guard.** A full-page scan that OCRs to ~2 Tibetan letters can score composite **1.0** (zero spellcheck errors, zero non-Tibetan ratio, line sanity inert). Threshold changes cannot fix this — needs T-10/T-13 minimum syllable or line-count floor.

These pages are **fixture candidates** when implementing T-10/T-11/T-13: a change is successful when they **escalate** (enter the AI loop) or **needs_review**, not auto-accept.

### Interim threshold (2026-06)

Default **accept raised to 0.9** so Phase B smoke on `pages_for_ocr_test.pdf` escalates pages in the 0.86–0.97 band into the AI loop. Override without code change:

```bash
python -m app.ocr_assist.run_job book.pdf --threshold-accept 0.9 --threshold-reject 0.5 --enable-ai -v
```

Re-calibrate in T-10 after AI smoke; do not treat 0.9 as production-final.

---

## Labeled failure pages (human ground truth)

Human label: **should not auto-accept** (should fail / escalate / needs review).

| Page | Human issue | Machine (Phase A) | Composite | Key signals | Relevant tickets |
|------|-------------|-------------------|-----------|-------------|------------------|
| **19** | **First line of page dropped** — OCR text starts mid-page; content missing vs image | **accept** | 0.974 | `line_count_sanity=1.0`; BDRC `line_count=8` (neighbors 16–18: 14–15 lines) | **T-13** (baseline would flag short page); may need stronger rule than ratio deviation alone |
| **17** | **`ཨཨཨ…` repetition** — known OCR failure signal for this text | **accept** | 0.968 | `non_tibetan_char_ratio=0`; low structural penalty despite obvious garbage run on line 3 | **T-10** (calibration); consider new **repetition / entropy** signal (not yet ticketed) |
| **14** | **Latin `S` in all-Tibetan context** — OCR contamination; should alarm | **accept** | 0.886 | `non_tibetan_char_ratio≈0.019`; `non_tibetan_penalty≈0.005` — still above 0.85 | **T-10**, **T-11** (presence-based contamination rule on Tibetan-only pages) |

### Page 19 — dropped first line

- **Human:** First line visible on the page image is missing from OCR output.
- **Artifact:** `page-019/attempts/01/ocr.txt` begins with `ལྡང་ཚེ་བརྫོང་ན་ཇི་ཁྱིན…` (8 lines total).
- **Neighbor line counts (BDRC `line_count`):** pages 16–18 → 14–15 lines; page 19 → **8 lines**.
- **Scorer gap:** T-13 not wired; even when wired, one missing line on an ~8-line page vs a ~14-line median is only a moderate sanity hit — may still accept unless combined with other rules.

### Page 17 — `ཨ` repetition

- **Human:** Line containing extended `ཨ་ཨ་ཨ…` / `ཨཨཨ…` runs indicates BDRC failed; must not auto-accept.
- **Artifact:** `page-017/attempts/01/ocr.txt` line 3 (long `ཨ` repetition block).
- **Scorer gap:** Phase-1 structural rules do not treat repetition as a hard failure; composite **0.968**. No non-Tibetan chars → Latin guardrails (T-11) do not help.

### Page 14 — Latin contamination

- **Human:** Stray Latin **`S`** in otherwise Tibetan page — obvious OCR mistake.
- **Artifact (job `4bed0eb14c9f`):** `page-014/attempts/01/ocr.txt` — verify `S` against image; file also contains Devanagari (`ऽ`), `+`, and other non-Tibetan scripts in mantra blocks. `non_tibetan_char_ratio≈1.9%`, composite **0.886** → still **accept**.
- **Scorer gap:** Same as stray-letter case — ratio dilutes on long pages; no hard floor for “any Latin in Tibetan-only pecha.”

---

## Additional notes from the same job

Worth tracking for calibration even though not primary fixtures:

| Page | Note | Composite | Decision |
|------|------|-----------|----------|
| 2 | Latin **`M`** on line 20 (`༎ཨེའ་།M`) | 0.894 | accept |
| 6 | Latin **`M`** in OCR | 0.906 | accept |
| 15 | Latin **`H`** in OCR | 0.903 | accept |
| 20 | Only **1 line** in OCR (likely severe drop / partial page) | 1.000 | accept |

Pattern: **scattered Latin letters and short pages routinely auto-accept** under default thresholds.

---

## Scorer behavior reference (for implementers)

### Non-Tibetan characters

```text
non_tibetan_penalty = W_NON_TIBETAN (0.25) × (non_tibetan_chars / total_non_space_chars)
```

- One Latin letter on a ~500-character page ≈ 0.0005 composite penalty — negligible.
- **Proposed direction (T-11 / T-10):** hard floor or fixed penalty when `non_tibetan_count >= 1` on pages **not** flagged `expect_mixed_script`.

### Line count

```text
line_count_sanity = 1.0   # when expected_line_count is None (current default)
```

- Runner passes BDRC `len(lines)` but **never** sets `expected_line_count`.
- **T-13:** rolling median from accepted pages; page 19 vs median ~14 lines → sanity ≈ 0.43 if baseline were active — meaningful, but first pages in job still unprotected.

### Encoding errors

- `encoding_error_count > 0` forces **escalate** or **reject**, not accept — but Latin `S` is not an encoding error.

---

## Acceptance criteria for future tickets

When T-10 / T-11 / T-13 land, re-run Phase A on the same PDF and expect:

- [ ] **Page 14** — does not auto-accept (contamination).
- [ ] **Page 17** — does not auto-accept (`ཨ` repetition); may require a new signal beyond current T-11 scope.
- [ ] **Page 19** — does not auto-accept (missing first line / short page vs job baseline).

Optional regression set: pages 2, 6, 15 (stray Latin letters).

---

## Suggested order of work (from these findings)

1. **T-13** — wire `expected_line_count` (helps page 19 and page 20).
2. **T-11 layer 1** — Tibetan-only composite + contamination hard floor (helps pages 14, 2, 6, 15).
3. **T-10** — calibrate thresholds on this PDF with human labels above.
4. **New signal (optional)** — repetition / run-length detector for `ཨ`-stack garbage (page 17); not yet in plan — file issue when prioritizing.

---

## Related paths

```text
backend/jobs/4bed0eb14c9f/page-014/attempts/01/{ocr.txt, quality.json}
backend/jobs/4bed0eb14c9f/page-017/attempts/01/{ocr.txt, quality.json}
backend/jobs/4bed0eb14c9f/page-019/attempts/01/{ocr.txt, quality.json}
```

Re-run command (Phase A):

```bash
cd backend
python -m app.ocr_assist.run_job pages_for_ocr_test.pdf \
  --jobs-root ./jobs \
  --model Woodblock \
  -v
```
