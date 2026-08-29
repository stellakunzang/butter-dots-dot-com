# Interactive OCR — Local AI Smoke & Vision A/B

**Companion to:** [INTERACTIVE_OCR_PLAN.md](INTERACTIVE_OCR_PLAN.md), [INTERACTIVE_OCR_WORKFLOW.md](INTERACTIVE_OCR_WORKFLOW.md)  
**Purpose:** Step-by-step guide for validating the **AI loop** locally (Phases B–E). Phase A (BDRC-only scorer calibration) is complete — thresholds and regression fixtures live in the plan (§ Quality scorer calibration) and `backend/tests/test_ocr_calibration.py`.

**When to use this:** After the integration branch includes T-05–T-07, settings plumbing, provider abstraction, and scorer calibration.

---

## What you're validating


| Layer                                 | What it does                                      | API cost?                            |
| ------------------------------------- | ------------------------------------------------- | ------------------------------------ |
| BDRC OCR + quality scorer             | Per-page accept / escalate / reject               | No                                   |
| Diagnostician (Anthropic)             | Retry with settings, Sanskrit accept, needs-human | Yes — up to 2 calls per bad page     |
| Vision fallback (Anthropic or Gemini) | Read image directly when BDRC fails               | Yes — at most 1 call per failed page |
| Job store                             | Persist attempts, verdicts, vision transcripts    | No                                   |


You're **not** required to use the old full-job `--enable-ai` path for vision A/B
anymore — the local `/ocr-assist` UI can **Compare vision** on a single page after
BDRC. This guide still covers CLI Phases B–E for diagnostician smoke and cost
checks.

**Also see:** root README § Interactive OCR CLI / browser UI.

---

## Prerequisites

### 1. Branch and backend env

```bash
git checkout feat/interactive-ocr   # or your PR2 branch after merge
cd backend
source venv/bin/activate
```

### 2. BDRC models (required for any OCR run)

```bash
python scripts/download_models.py
```

Confirm `backend/OCRModels/` contains at least `Woodblock` and `Modern`.

### 3. API keys

Add to `backend/.env` (never commit):

```bash
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...   # only if testing Gemini vision
```

Optional: `DIAGNOSTICIAN_PROVIDER`, `VISION_OCR_PROVIDER`.

### 4. Gemini (vision A/B)

`google-genai` is pinned in `backend/requirements.txt` (with `httpx>=0.28.1`).
A normal `pip install -r requirements.txt` is enough — no separate install step.

Set `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) in `backend/.env` when testing Gemini.

### 5. Test PDF

Use your real target text. For cheaper iteration, extract 3–5 known-problem pages into a small PDF. Don't commit copyrighted material.

---

## Phase A — BDRC-only baseline ✅ complete

Scorer calibration for **scanned pecha** is done (T-10/T-11 layer 1/T-13). Re-verify without API keys:

```bash
cd backend
venv/bin/python -m app.ocr_assist.run_job /path/to/sample.pdf \
  --jobs-root ./jobs --model Woodblock -v
```

Regression: `venv/bin/pytest tests/test_ocr_calibration.py -q`

See [INTERACTIVE_OCR_PLAN.md § Quality scorer calibration](INTERACTIVE_OCR_PLAN.md#quality-scorer-calibration-t-10) for thresholds, hard floors, and false-accept counts.

---

## Phase B — Full Claude loop (diagnostician + vision)

```bash
cd backend
python -m app.ocr_assist.run_job /path/to/sample.pdf \
  --jobs-root ./jobs \
  --enable-ai \
  --diagnostician-provider anthropic \
  --vision-provider anthropic \
  -v
```

Watch logs for `cache_read > 0` on diagnostician retries (T-06) and vision calls only on failed pages (T-07).

**Pass criteria (T-06 / T-07 smoke):**

- [ ] Bad page produces `ai_verdict.json` with `retry_with_settings` and updated `settings.json`.
- [ ] At least one bad page triggers vision; `vision_ocr.json` exists.
- [ ] Clean page: no vision call.
- [ ] Vision accept → `final.txt` from vision, notes mention `vision fallback`.
- [ ] Vision fail → `needs_review`, both BDRC and vision transcripts on disk.

**Known gap:** API errors currently crash the page run rather than falling back to `needs_review` (T-12).

---

## Phase C — Diagnostician Sanskrit smoke (T-06)

Pick a page that is **mostly Sanskrit/mantra** and scores below accept on first OCR. Same command as Phase B.

**Pass criterion:**

- [x] `ai_verdict.json` contains `"tool": "accurate_as_sanskrit_accept"` OR documented rationale for retry instead.

---

## Phase D — Gemini vs Claude vision A/B

Run the same PDF twice; only change `--vision-provider`. Use separate `--jobs-root` dirs.

Compare pages where both runs invoked vision. Record results in `docs/planning/INTERACTIVE_OCR_VISION_AB.md` (create during the run).

---

## Phase E — Cost sanity check

For a 100-page pecha where 90% accept on first OCR: ~10 pages × (2 diag + 1 vision) ≈ 30 API calls. Run a 5-page sample first and check provider dashboards.

---

## Filesystem cheat sheet


| Path                          | Meaning                                |
| ----------------------------- | -------------------------------------- |
| `manifest.json`               | Job metadata, page count               |
| `baseline_settings.json`      | Frozen job baseline                    |
| `page-NNN/settings.json`      | Per-page settings (mutated by retries) |
| `attempts/NN/ocr.txt`         | BDRC output                            |
| `attempts/NN/quality.json`    | Scorer breakdown + composite           |
| `attempts/NN/spellcheck.json` | Phase-1/2 errors for HITL highlights   |
| `attempts/NN/ai_verdict.json` | Diagnostician verdict                  |
| `vision_ocr.json`             | Vision transcript                      |
| `final.txt`                   | Accepted text                          |


**HITL UI:** `/ocr-assist` shows spellcheck-style underlines (red structural / yellow unknown) from `spellcheck.json`. Tunables and rationale: [INTERACTIVE_OCR_PLAN.md](INTERACTIVE_OCR_PLAN.md) § Living decisions.


---

## Suggested order

1. ~~Phase A~~ — done; run `test_ocr_calibration.py` to confirm.
2. Phase B on a small sample — full loop + artifacts.
3. Phase C if you have a Sanskrit-heavy page.
4. Phase D on pages that triggered vision in Phase B.
5. Phase E — then run the full target PDF.

---

## Quick command reference

```bash
# BDRC only (calibrated scorer)
python -m app.ocr_assist.run_job book.pdf --jobs-root ./jobs -v

# Claude diagnostician + Claude vision
python -m app.ocr_assist.run_job book.pdf --jobs-root ./jobs --enable-ai -v

# Claude diagnostician + Gemini vision
python -m app.ocr_assist.run_job book.pdf --jobs-root ./jobs --enable-ai --vision-provider gemini -v
```

