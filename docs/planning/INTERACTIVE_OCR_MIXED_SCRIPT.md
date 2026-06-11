# Mixed-script pages — guardrails for the OCR retry loop

**Companion to:** [INTERACTIVE_OCR_PLAN.md](INTERACTIVE_OCR_PLAN.md)  
**Status:** Ticket **T-11** in [INTERACTIVE_OCR_PLAN.md](INTERACTIVE_OCR_PLAN.md) — not implemented.  
**Problem:** Legitimate English+Tibetan pages can trigger the AI retry loop (and vision fallback) even when BDRC got the Tibetan right, because the quality scorer treats all non-Tibetan characters the same as OCR garbage.

---

## What's happening today

### The scorer sees Latin, not intent

`non_tibetan_char_ratio` counts every non-Tibetan codepoint (Latin, digits, punctuation) over total non-whitespace characters. It does not distinguish:

- **Intentional English** (titles, transliteration lines, bilingual pecha)
- **Sanskrit** (partially handled via `sanskrit_adjusted_error_ratio` on structural errors)
- **OCR garbage** (Latin letters BDRC hallucinated inside Tibetan lines)

For a page that's ~40% intentional English with clean Tibetan OCR:

```
non_tibetan_penalty = 0.25 × 0.40 = 0.10
→ composite ≈ 0.90 if Tibetan structure is clean
→ decide() → accept (no retry)
```

Retries only kick in when non-Tibetan content pushes composite **below 0.85** (~60%+ non-Tibetan) *or* structural errors on the Tibetan portion pull the score into the escalate band (0.5–0.85).

So **moderate** bilingual pages often pass silently. The waste case is:

| Pattern | What happens | Waste |
|---------|----------------|-------|
| 20–50% English + noisy Tibetan OCR | Escalate → diagnostician retries | Settings won't remove English |
| Scattered Latin inside Tibetan lines | Escalate → retries | Legitimate — may be OCR confusion |
| Mostly English page with some Tibetan | Reject or escalate → vision | Vision may help; BDRC retries won't |
| Clean Tibetan + English blocks | Often accept | None |

### Soft guardrails that exist

1. **Diagnostician prompt** mentions mixed scripts and `needs_human` — but it's LLM-judgment, costs an API call, and `needs_human` still invokes vision fallback afterward.
2. **Spellcheck path** (copy-paste / PDF export) emits `non_tibetan_skipped` info — the OCR quality scorer does **not** use this; it scores raw OCR text.
3. **Sanskrit detector** strips Sanskrit-likely syllables from the structural error numerator — no equivalent for English/Latin blocks.

### Hard guardrails that do **not** exist

- No Tibetan-only quality score for accept/retry decisions
- No Latin-block vs scattered-Latin detection
- No runner preflight to skip the diagnostician when English is expected
- No job-level `expect_mixed_script` baseline flag
- No cap on API calls when `non_tibetan_char_ratio` is high but Tibetan structure is clean

---

## T-11 — Mixed-script guardrails

(Full ticket spec lives in [INTERACTIVE_OCR_PLAN.md](INTERACTIVE_OCR_PLAN.md) § T-11. Design detail below.)

**Deploy:** `prod` (local computation only — reduces API cost)  
**Depends on:** T-03 (quality scorer), T-05 (runner)

### Goal

Stop burning diagnostician + vision API calls on pages where the failure mode is "this page has English on it," not "BDRC misread the Tibetan."

### Approach (recommended — two layers)

#### Layer 1 — Tibetan-only score (local, ship first)

Add a parallel score path in `quality.py`:

```python
tibetan_text = extract_tibetan(ocr_text)  # already in normalizer.py
tibetan_quality = score_page(tibetan_text, spellcheck(tibetan_text), ...)
```

Expose on `PageQuality`:

- `tibetan_only_composite_score`
- `non_tibetan_char_ratio` (unchanged — still useful signal)

**Decision rule change in `decide()` or runner:**

```
if non_tibetan_char_ratio >= MIXED_SCRIPT_THRESHOLD (e.g. 0.15)
   and tibetan_only_composite >= accept:
       → accept page (or accept_tibetan_portion — see open question)
       → skip diagnostician entirely
```

This is deterministic, testable, and free.

#### Layer 2 — Latin block detector (local)

Distinguish contiguous Latin runs from scattered single letters inside Tibetan lines:

- **Block signal:** 3+ consecutive Latin letters, or a line that's >80% Latin → likely intentional English
- **Scatter signal:** isolated ASCII within Tibetan lines → likely OCR noise

Use block ratio to **lower** non-Tibetan penalty (or zero it out) when blocks dominate; keep full penalty when scatter dominates.

### Open questions (decide during T-10/T-11 smoke)

1. **Accept semantics:** On a bilingual accept, does `final.txt` keep the full OCR output (Tibetan + English) or Tibetan-only? Default lean: keep full text — the user wants the whole page.
2. **Threshold:** `MIXED_SCRIPT_THRESHOLD` should be calibrated on the target PDF alongside T-10, not guessed.
3. **Vision fallback:** When Layer 1 accepts on Tibetan-only score but full composite is low, skip vision too? Lean: yes — vision won't remove English either.
4. **Job baseline flag:** `expect_mixed_script: true` on jobs known to be bilingual (e.g. pecha with facing translation). Lowers threshold or forces Layer 1 on every page.

### Out of scope

- Segmenting the page image into Tibetan vs English regions for separate OCR
- PREPARE feature's full style detection ([PREPARE_FEATURE.md](PREPARE_FEATURE.md)) — different pipeline, but could feed `expect_mixed_script` later

### Acceptance criteria

- [ ] `PageQuality` includes `tibetan_only_composite_score`
- [ ] Bilingual fixture page (Tibetan + English blocks, clean OCR) auto-accepts without calling diagnostician
- [ ] Scattered-Latin garbage fixture still escalates to diagnostician
- [ ] Unit tests for both paths; no regression on pure-Tibetan fixtures
- [ ] Document chosen thresholds in `INTERACTIVE_OCR_CALIBRATION.md` (T-10 output)

### Estimated effort

One PR — mostly `quality.py` + runner preflight + tests. Layer 2 (block detector) can be a follow-up PR if Layer 1 solves 80% of the waste on your target text.

---

## What to watch during local smoke (before T-11)

When running [INTERACTIVE_OCR_LOCAL_SMOKE.md](INTERACTIVE_OCR_LOCAL_SMOKE.md), flag pages where:

- `quality.json` → `non_tibetan_char_ratio` > 0.15
- `quality.json` → `structural_error_ratio` is low (Tibetan looks fine)
- `attempts/` has 2+ entries with `retry_with_settings` verdicts
- Human review: Tibetan portion looks correct in `ocr.txt`

Record those page numbers — they're the calibration set for T-11.

---

## Relationship to other work

| Work | Relationship |
|------|----------------|
| T-10 threshold calibration | Tune `MIXED_SCRIPT_THRESHOLD` and weights on real bilingual pages |
| T-02 Sanskrit detector | Same pattern — strip known-good non-Tibetan structural false positives |
| PREPARE feature | Long-term: detect English Body vs Tibetan Body styles upstream |
| T-09 review UI | Show `tibetan_only_composite` alongside full composite so reviewers see why a page auto-accepted or skipped AI |
