# Interactive OCR — Local Smoke & Vision A/B Plan

**Companion to:** [INTERACTIVE_OCR_PLAN.md](INTERACTIVE_OCR_PLAN.md), [INTERACTIVE_OCR_WORKFLOW.md](INTERACTIVE_OCR_WORKFLOW.md)  
**Purpose:** Step-by-step guide for trying the full AI loop locally after the integration branch merges. Covers Claude diagnostician + vision fallback, and the Gemini vs Claude vision comparison (#3 from the implementation sequence).

**When to use this:** After `feat/interactive-ocr` (or your merge target) includes T-05–T-07, settings plumbing (#1), and provider abstraction (#2).

---

## What you're validating

| Layer | What it does | API cost? |
|-------|----------------|-----------|
| BDRC OCR + quality scorer | Per-page accept / escalate / reject | No |
| Diagnostician (Anthropic) | Retry with settings, Sanskrit accept, needs-human | Yes — up to 2 calls per bad page |
| Vision fallback (Anthropic or Gemini) | Read image directly when BDRC fails | Yes — at most 1 call per failed page |
| Job store | Persist attempts, verdicts, vision transcripts | No |

You're **not** validating T-09 (UI) or T-08 (DOCX export) here — CLI + filesystem inspection only.

---

## Prerequisites

### 1. Branch and backend env

```bash
git checkout feat/interactive-ocr   # or whatever branch has the merged work
cd backend
source venv/bin/activate          # or: python -m venv venv && pip install -r requirements.txt
```

### 2. BDRC models (required for any OCR run)

```bash
cd backend
python scripts/download_models.py
```

Confirm `backend/OCRModels/` contains at least `Woodblock` and `Modern`. Default BDRC model comes from `OCR_MODEL_NAME` in `backend/.env` (defaults to `Woodblock`).

### 3. API keys

Add to `backend/.env` (never commit):

```bash
# Required for --enable-ai with default providers
ANTHROPIC_API_KEY=sk-ant-...

# Only if testing Gemini vision
GEMINI_API_KEY=...
# or: GOOGLE_API_KEY=...
```

Optional provider overrides (also available as CLI flags):

```bash
DIAGNOSTICIAN_PROVIDER=anthropic    # only anthropic today
VISION_OCR_PROVIDER=anthropic         # or gemini
```

### 4. Gemini optional dependency (vision A/B only)

`google-genai` is **not** pinned in `requirements.txt` because it currently wants `httpx>=0.28`, which conflicts with the project's FastAPI test stack. For a **local-only** Gemini trial:

```bash
pip install 'google-genai>=1.0.0'
```

If `pip` warns about httpx conflicts, that's expected for now. If API tests break in the same venv, use a separate venv for Gemini experiments, or upgrade fastapi/starlette/httpx together in a follow-up ticket.

### 5. Test PDF

Use your real target text. For cheaper iteration:

- Extract **3–5 known-problem pages** (bad BDRC, Sanskrit blocks, skew, faded scans) into a small PDF.
- Keep one **clean page** in the mix to confirm vision is *not* called on accepts.

Name them predictably, e.g. `tests/fixtures/smoke/target-sample-5p.pdf` (don't commit if copyrighted).

---

## Phase A — BDRC-only baseline (no API keys)

Confirms settings plumbing and quality scores before spending on LLM calls.

```bash
cd backend
python -m app.ocr_assist.run_job /path/to/sample.pdf \
  --jobs-root ./jobs \
  --model Woodblock \
  -v
```

**Inspect:** `jobs/<job_id>/`

```
page-001/
  image.png
  settings.json
  attempts/01/{ocr.txt, quality.json}
  final.txt              # present if auto-accepted
```

**Record per page:**

| Page | composite | decision | Notes |
|------|-----------|----------|-------|
| 1 | | accept / needs_review | |

**Pass criteria:**

- Clean pages → `accept`, `final.txt` written.
- Bad pages → `needs_review`, attempts persisted, no `final.txt`.
- `settings.json` reflects `--model` baseline.

**Optional — verify retry settings actually change OCR:** Pick one bad page, manually edit `page-NNN/settings.json` (e.g. `"k_factor": 3.5`, `"model_variant": "Ume"`), delete any attempts/final, re-run with a one-page PDF. OCR output should differ from the baseline run.

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

Watch logs for:

- `diagnostician usage: ... cache_read=...` — second retry on the **same page** should show `cache_read > 0` (T-06 acceptance).
- `vision_ocr usage: ...` — only on pages that ended up needing vision.

**Inspect a retried page** (`attempts/` has 02+):

```
attempts/
  01/{ocr.txt, quality.json, ai_verdict.json}
  02/...
vision_ocr.json          # if vision ran
vision_quality.json
notes.md                 # if finalized via vision or Sanskrit accept
```

**Pass criteria (T-06 / T-07 smoke):**

- [ ] Bad page produces `ai_verdict.json` with `retry_with_settings` and updated `settings.json`.
- [ ] At least one bad page triggers vision; `vision_ocr.json` exists.
- [ ] Clean page: no vision call (no `vision_ocr.json`).
- [ ] If vision clears threshold: `final.txt` matches vision text, notes mention `vision fallback`.
- [ ] If vision fails: `needs_review`, both BDRC attempts and vision transcript on disk.

**Known gap:** API errors (`DiagnosticianError`, network failures) currently **crash the page run** rather than falling back to human review. If a call fails, note the error and continue manually — error handling is a follow-up.

---

## Phase C — Diagnostician Sanskrit smoke (T-06)

Pick a page that is **mostly Sanskrit/mantra** and scores below accept on first OCR.

```bash
# Same as Phase B; focus on one page in the job dir afterward
```

**Pass criterion:**

- [ ] `ai_verdict.json` contains `"tool": "accurate_as_sanskrit_accept"` OR you can explain why retry was chosen instead (document rationale — helps T-10).

---

## Phase D — Gemini vs Claude vision A/B (#3)

Run the **same PDF** twice with identical BDRC/diagnostician settings; only change the vision provider.

### Run 1 — Claude vision (control)

```bash
python -m app.ocr_assist.run_job /path/to/sample.pdf \
  --jobs-root ./jobs/claude-vision \
  --enable-ai \
  --vision-provider anthropic \
  -v
```

### Run 2 — Gemini vision

```bash
python -m app.ocr_assist.run_job /path/to/sample.pdf \
  --jobs-root ./jobs/gemini-vision \
  --enable-ai \
  --vision-provider gemini \
  -v
```

Use separate `--jobs-root` dirs so job IDs don't collide and you can diff side-by-side.

### Pages to compare

Only pages where **both runs invoked vision** (have `vision_ocr.json`). For each:

| Page | BDRC composite | Claude vision composite | Gemini vision composite | Human ground truth |
|------|----------------|-------------------------|-------------------------|-------------------|
| | | | | accept / reject |

**Comparison method (manual is fine):**

1. Open `page-NNN/image.png` alongside `vision_ocr.json` from each job.
2. Compare `vision_ocr.json` → `text` against the image (and against copy-paste ground truth if you have it).
3. Compare `vision_quality.json` → `composite_score` — same scorer, so scores are comparable.
4. Note which transcript you'd ship to a human reviewer.

**What "Gemini wins" looks like:**

- Higher composite on pages BDRC mangled badly.
- Fewer encoding / non-Tibetan char errors in `vision_quality.json` breakdown.
- Transcript visibly matches the image where Claude hallucinated or dropped lines.

**What to record:** Save a short note in `docs/planning/INTERACTIVE_OCR_VISION_AB.md` (create after the run) with page numbers, winner, and 1–2 sentence reason per page. That feeds T-10 threshold work and the provider default decision.

---

## Phase E — Cost sanity check

Rough per-page upper bound with `--enable-ai` and `max_attempts=3` (default):

- Diagnostician: up to **2** calls per bad page (not called on last attempt or on accept).
- Vision: up to **1** call per page that still needs review after BDRC loop.

For a 100-page pecha where 90% accept on first OCR: ~10 pages × (2 diag + 1 vision) = ~30 API calls, not 300.

Run your 5-page sample first and check Anthropic/Gemini dashboards before running the full book.

---

## Filesystem cheat sheet

| Path | Meaning |
|------|---------|
| `manifest.json` | Job metadata, page count |
| `baseline_settings.json` | Frozen job baseline (never mutated by retries) |
| `page-NNN/settings.json` | Per-page settings (mutated by diagnostician overrides) |
| `attempts/NN/ocr.txt` | BDRC output for that attempt |
| `attempts/NN/quality.json` | Scorer breakdown + composite |
| `attempts/NN/ai_verdict.json` | Diagnostician verdict |
| `vision_ocr.json` | Vision provider transcript + notes |
| `vision_quality.json` | Same scorer applied to vision text |
| `final.txt` | Accepted text (BDRC, vision, or Sanskrit accept) |
| `notes.md` | Provenance (vision fallback, Sanskrit rationale, etc.) |

---

## Suggested order of operations

1. Phase A on 5-page sample — confirm BDRC + scores make sense.
2. Phase B on same sample — confirm full loop + filesystem artifacts.
3. Phase C if you have a Sanskrit-heavy page.
4. Phase D on pages that triggered vision in Phase B.
5. Phase E review — then decide default `VISION_OCR_PROVIDER` for your corpus.
6. Only then run the full target PDF (or kick off T-10 calibration).

---

## Follow-ups (out of scope for this smoke)

- **Mixed-script guardrails (T-11):** See [INTERACTIVE_OCR_MIXED_SCRIPT.md](INTERACTIVE_OCR_MIXED_SCRIPT.md). Watch for wasted retries on bilingual pages during this smoke.
- **Error handling:** Catch `DiagnosticianError` / provider API errors → `needs_review` instead of crash.
- **Gemini in CI:** Resolve httpx/fastapi pin conflict; add `google-genai` to requirements or optional extra.
- **CLI gaps:** `--max-attempts`, `--pages 3,7,12`, single-page re-run without re-creating job.
- **T-08 / T-09:** DOCX export and review UI.
- **T-10:** Tune `accept`/`reject` thresholds using human labels from this smoke.

---

## Quick command reference

```bash
# BDRC only
python -m app.ocr_assist.run_job book.pdf --jobs-root ./jobs -v

# Claude diagnostician + Claude vision
python -m app.ocr_assist.run_job book.pdf --jobs-root ./jobs --enable-ai -v

# Claude diagnostician + Gemini vision
python -m app.ocr_assist.run_job book.pdf --jobs-root ./jobs --enable-ai --vision-provider gemini -v

# Run tests before committing smoke notes
cd backend && venv/bin/pytest -m "not slow" -q
```
