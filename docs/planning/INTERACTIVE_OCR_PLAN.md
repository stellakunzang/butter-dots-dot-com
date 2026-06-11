# Interactive Page-by-Page OCR with AI Assistance

**Status:** In progress on `feat/interactive-ocr` — core loop implemented (T-01–T-07, T-05b, T-07b); UI, calibration, and guardrails not yet done.
**Goal:** Convert a Tibetan text into a Word document, one page at a time, where pages that come out clean auto-advance and pages that don't get an AI-assisted retry loop and (if still bad) surface to a human. No more global-tweak-that-breaks-other-pages.
**Scope:** Local-only for now. Single-user workflow. Future use case: photos of physical books (not yet in scope but shouldn't be architecturally blocked).

**Related docs:**
- [INTERACTIVE_OCR_WORKFLOW.md](INTERACTIVE_OCR_WORKFLOW.md) — branching, chat workflow
- [INTERACTIVE_OCR_LOCAL_SMOKE.md](INTERACTIVE_OCR_LOCAL_SMOKE.md) — post-merge local testing + vision A/B
- [INTERACTIVE_OCR_MIXED_SCRIPT.md](INTERACTIVE_OCR_MIXED_SCRIPT.md) — T-11 design detail

---

## Deployment posture

Anything that calls a paid LLM API must **not** run in production yet — unbounded per-page costs against an unmetered surface is exactly the failure mode we're avoiding. But several tickets are valuable on their own and safe to ship.

Each ticket below carries one of three tags:

- **`deploy: prod`** — pure local computation, no API cost, improves existing functionality. Safe to ship behind the normal merge flow.
- **`deploy: local-only`** — workflow/state that's only intended for local use right now. The code can live in `main` (it doesn't hurt anything sitting there), but the entry points stay off in prod via env flag or simply by not exposing routes.
- **`deploy: behind-flag`** — anything that calls an LLM API (Anthropic and/or Gemini). Stays local-only until auth lands; then gated by an admin-only flag (e.g., `FEATURE_AI_OCR_ASSIST=true` + admin role check). Even after gating, consider a per-job cost cap.

When auth exists, the plan is: one feature flag (`ai_ocr_assist`) checked at the API layer, restricted to admin users. UI surfaces hide the AI controls when the flag is off. Cost cap (e.g., max-N-API-calls-per-job, or max-spend-per-day) enforced server-side regardless of role.

### What can ship to prod right now

- **T-01** — OCR engine improvements ✅
- **T-02** — Sanskrit detector ✅
- **T-02b** — Surface Sanskrit signal in existing spellcheck API/UI
- **T-03** — Page quality scorer ✅
- **T-05b** — Per-page BDRC settings plumbing ✅
- **T-08** — Clean DOCX export with page numbers

### What stays local-only / behind-flag

- **T-04, T-05** — Job store and runner ✅ (code merged; workflow not prod-ready)
- **T-06, T-07, T-07b** — Diagnostician, vision fallback, provider abstraction ✅ (API cost — gated)
- **T-09** — Interactive UI
- **T-10, T-16** — Calibration and vision A/B (local exercises)
- **T-11** — Mixed-script guardrails (local computation; reduces API waste once shipped)

---

## Background

Two existing projects supply the parts:

- **`butter-dots-dot-com`** (this repo): FastAPI + Next.js. BDRC OCR at `backend/BDRC/`, spellcheck at `backend/app/spellcheck/`, interactive OCR loop at `backend/app/ocr_assist/` (job store, runner, quality scorer, LLM providers). DOCX exporter at `backend/app/pdf/docx_exporter.py`.
- **`../tibetan-ocr-app`** (sibling repo): PySide6 desktop app. Has the more recently improved OCR (rotation-angle fix, TPS singularity guard, `split_tall_contours`, multi-channel image handling) and a `DocxExporter` with `Page N` headings in Tibetan Machine Uni 14pt. No spell-check.

This plan lives in `butter-dots-dot-com` because that's where the spell-check and the web stack are. The sibling repo stays as upstream for OCR engine improvements.

---

## Constraints from current state

- **Corpus is unpopulated.** Phase 2 of spellcheck (dictionary lookup) is effectively a no-op right now. Quality scoring must rely on **Phase 1 only** (structural validation, pattern checks, stacking rules) plus OCR-level signals (non-Tibetan char ratio, line count sanity, BDRC diagnostics). When the corpus is later populated, Phase 2 becomes an additional weighted input — the score interface should already accommodate it.
- **Sanskrit transliteration appears in real texts.** Mantras, dharanis, and proper names deliberately break Tibetan stacking rules. Without handling, every Sanskrit run will trip the retry loop. Handled at two layers (local detector + Claude tiebreaker — see below).

---

## Approach

### Per-page iteration loop

```
load page image
  ↓
OCR with page's current settings (start = baseline)
  ↓
compute quality score
  ↓
score >= accept_threshold?  ── yes ──→ save page, next page
  ↓ no
attempt < max_attempts (default 3)?
  ↓ yes
ask LLM diagnostician: { image, ocr_text, quality breakdown, prior attempts }
  verdict ∈ {
    "retry_with_settings": { k_factor, rotate, crop, model_variant, ... },
    "accurate_as_sanskrit_accept",         // stops the loop cleanly
    "needs_human": "<reason>"
  }
  ↓
apply verdict, loop
  ↓ no (attempts exhausted or needs_human)
vision transcriber reads image directly (Anthropic or Gemini — T-07)
  ↓
score vision transcript; accept or attach for human review
  ↓ still not accepted
surface to human with: image, BDRC attempts, vision transcript, quality breakdown
human action ∈ { accept, edit, skip, try different model variant, change settings }
```

### Why this avoids the global-tweak regression

Settings are **per-page**, never per-job. Each page has its own settings struct that starts as a copy of the job's baseline. Retries mutate only the page's copy. The baseline is frozen for the duration of the job. A page that needed `k_factor=3.0` doesn't propagate that to the next page. Every page's final settings, OCR output, and verdicts are persisted, so a re-run of the same page is deterministic.

### Quality score (Phase-1-only for now)

Weighted blend of:

- **`non_tibetan_char_ratio`** — proportion of non-Tibetan codepoints in the page. Strong "OCR confused" signal. Latin letters and unexpected ASCII punctuation drive this.
- **`structural_error_ratio`** — Phase-1 spell-check errors / total syllables, weighted by severity (critical > error > warning > info). Excludes `unknown_word` (Phase 2) for now.
- **`sanskrit_adjusted_error_ratio`** — same as above but with Sanskrit-flagged syllables removed from the numerator.
- **`line_count_sanity`** — deviation from the page's expected line count (configurable, e.g., median of accepted pages so far).
- **`encoding_error_count`** — hard floor; any non-zero count is suspicious because it indicates wrong-codepoint substitution.

Two thresholds: `accept` (no AI) and `reject` (too damaged to retry profitably). Pages in between enter the AI retry loop. Thresholds are calibrated against real pages (T-10). **Known gap:** intentional English on bilingual pages can trigger retries — see T-11.

### Sanskrit handling

**Local detector** (T-02): a pattern-based classifier that runs against each Phase-1-flagged syllable. Looks for:
- Telltale codepoints: ཾ (U+0F7E anusvara), ཿ (U+0F7F visarga), ྂ, ྃ
- Subjoined consonants in non-Tibetan combinations (e.g., subjoined ya/ra/la/va patterns that violate Tibetan stacking)
- Three-consonant stacks
- **Clustering bonus**: Sanskrit usually runs in contiguous blocks. If neighboring syllables are also flagged Sanskrit-like, increase confidence.

Output: per-syllable `sanskrit_likelihood ∈ [0, 1]`. The quality scorer uses this to compute `sanskrit_adjusted_error_ratio`.

**LLM tiebreaker** (T-06): when the AI diagnostician is consulted, one of its allowed verdicts is `accurate_as_sanskrit_accept`. This stops the retry loop without forcing a transcription rewrite.

### AI role

LLM providers (Anthropic default; Gemini optional for vision — T-07b) play two distinct roles, both invoked only when the local quality score is below `accept`:

1. **Quality diagnostician** (T-06) — given the image + OCR text + quality breakdown + prior attempts, returns one of the verdicts in the loop diagram. Most useful for: detecting skew/multi-column, recommending a different model variant (Modern vs Woodblock vs Ume), confirming Sanskrit content.
2. **Vision-OCR fallback** (T-07) — when BDRC retries don't converge (or diagnostician returns `needs_human`), a vision model reads the image directly. Not expected to beat BDRC on clean pages; expected to help on pathological pages (warped, faded ink, future physical-book photos). Mixed English+Tibetan pages may waste vision calls too — T-11 addresses this.

Both are wired via `backend/app/ocr_assist/providers/` and gated behind `--enable-ai` on the CLI. Env: `ANTHROPIC_API_KEY`, optional `GEMINI_API_KEY` + `VISION_OCR_PROVIDER=gemini`.

### Per-page state model

Filesystem-backed job directory (simpler than Postgres for a local tool, and inspectable by hand):

```
jobs/<job_id>/
  baseline_settings.json
  manifest.json                # page count, source file, status
  page-001/
    image.png
    settings.json              # page-local settings (baseline + overrides)
    attempts/
      01/{ocr.txt, quality.json, ai_verdict.json}
      02/...
    final.txt                  # accepted text
    final_quality.json
    notes.md                   # human notes if any
    vision_ocr.json            # vision fallback transcript (if consulted)
    vision_quality.json
  page-002/
    ...
  output.docx
```

This makes resume trivial (read manifest, find first non-final page) and per-page re-run trivial (delete `final.txt` and re-run that page only).

### Word document output

Extend the existing `docx_exporter.py` with a "clean export" mode that mirrors `tibetan-ocr-app/BDRC/Exporter.py:DocxExporter`:
- `Page N` heading per page
- Tibetan Machine Uni 14pt body
- Optional spell-check error highlighting as a separate toggle

Write incrementally as pages are accepted, not all-at-end. A crash mid-job preserves accepted pages.

---

## Open questions to revisit

1. **Model variant selection.** ✅ Lean confirmed: per-page setting; diagnostician may override via `retry_with_settings`. Implemented (T-05b).
2. **Vision fallback trigger.** ✅ Lean confirmed: automatic after retries exhaust or `needs_human`. Implemented (T-07).
3. **Vision provider default.** Run T-16 smoke A/B (Claude vs Gemini) on bad pages before picking a default.
4. **GitHub mirror.** Markdown-first; mirror to GH issues if useful.
5. **Bilingual page accept semantics.** Keep full OCR text (Tibetan + English) in `final.txt` when T-11 auto-accepts? Lean: yes — see [INTERACTIVE_OCR_MIXED_SCRIPT.md](INTERACTIVE_OCR_MIXED_SCRIPT.md).

---

## Tickets

Each ticket below is sized to be a single PR. Dependencies are noted. The order is the suggested implementation order but T-01 and T-02 can run in parallel.

### Status overview (2025-06)

| Ticket | Summary | Status |
|--------|---------|--------|
| T-01 | OCR engine port | ✅ Done |
| T-02 | Sanskrit detector | ✅ Done |
| T-02b | Sanskrit in spellcheck API/UI | ⬜ Not started |
| T-03 | Quality scorer | ✅ Done |
| T-04 | Job store | ✅ Done |
| T-05 | Runner (no AI) | ✅ Done |
| T-05b | BDRC settings plumbing | ✅ Done |
| T-06 | Diagnostician | ✅ Done (2 smoke tests pending) |
| T-07 | Vision fallback | ✅ Done (1 smoke test pending) |
| T-07b | LLM provider abstraction | ✅ Done |
| T-08 | DOCX export | ⬜ Not started |
| T-09 | Interactive UI | ⬜ Not started |
| T-10 | Threshold calibration | ⬜ Not started |
| T-11 | Mixed-script guardrails | ⬜ Not started |
| T-12 | Provider error resilience | ⬜ Not started |
| T-13 | Line-count sanity baseline | ⬜ Not started |
| T-14 | CLI ergonomics | ⬜ Not started |
| T-15 | Gemini optional dep / httpx | ⬜ Not started |
| T-16 | Local smoke + vision A/B | 📋 Doc ready — run after merge |

---

### T-01 — Port OCR engine improvements from `tibetan-ocr-app`

**Deploy:** `prod`
**Why:** Several failure modes that would otherwise trigger the retry loop are already fixed upstream. Pulling these forward reduces AI cost and human-review volume before any new code is written.

**Scope:**
- Port the following from `../tibetan-ocr-app/BDRC/` into `backend/BDRC/`:
  - `line_detection.py`: rotation-angle sign fix; `max_angle` raised to 2.0°; dead-code removal on high-angle path
  - `line_detection.py`: `split_tall_contours()` and its integration in the line extraction step
  - `image_dewarping.py`: collinearity check before TPS solve
  - `Inference.py`: `update_line_detection()` fix for `self.line_config`
  - `Runner.py`: explicit multi-channel image handling (grayscale, RGBA, CMYK+Alpha)
- Record the upstream commit SHA in a `backend/BDRC/UPSTREAM.md` for future syncs

**Out of scope:** Refactoring the BDRC code, changing model files, adding new preprocessing.

**Acceptance criteria:**
- [x] All listed fixes present in `backend/BDRC/`
- [x] Existing OCR endpoint still works on a known-good PDF (smoke test)
- [x] `UPSTREAM.md` records the synced-from commit SHA and lists the cherry-picked fixes
- [x] No spellcheck or DOCX behavior changes

**Dependencies:** none

---

### T-02 — Sanskrit-transliteration detector

**Deploy:** `prod`
**Why:** Sanskrit content deliberately breaks Tibetan stacking rules. Without this, Sanskrit blocks will dominate the structural error count and trigger pointless retries.

**Scope:**
- New module: `backend/app/spellcheck/sanskrit.py`
- Function `score_sanskrit_likelihood(syllable: TibetanSyllable, context: list[TibetanSyllable]) -> float` returning `[0, 1]`
- Detection signals:
  - Presence of ཾ (U+0F7E), ཿ (U+0F7F), ྂ (U+0F82), ྃ (U+0F83)
  - Subjoined ya/ra/la/va in patterns not allowed by Tibetan stacking rules
  - Three-consonant stacks
  - Clustering bonus: neighboring syllables also Sanskrit-flagged
- Unit tests with representative Tibetan-only syllables (score → low), known mantra fragments (score → high), borderline cases documented

**Out of scope:** Integration into the quality scorer (that's T-03). Wiring into the existing spellcheck API response (that's T-02b).

**Acceptance criteria:**
- [x] Module exists with the function signature above
- [x] Tests cover at least: pure Tibetan word (score < 0.1), classic mantra syllable (score > 0.7), ambiguous case (score in middle band)
- [x] No regression in existing spellcheck tests

**Dependencies:** none

---

### T-02b — Surface Sanskrit signal in existing spellcheck API/UI

**Deploy:** `prod`
**Why:** The Sanskrit detector from T-02 is immediately useful to today's spellcheck users — flagged words that are likely Sanskrit can be annotated as "probably OK" instead of looking like real errors.

**Scope:**
- Extend the spellcheck error payload (`backend/app/api/spellcheck.py`) to include `sanskrit_likelihood: float` and `likely_sanskrit: bool` per error
- Threshold for `likely_sanskrit` lives as a constant alongside the detector
- Frontend: in the spellcheck UI, render likely-Sanskrit errors with a distinct visual treatment (e.g., dotted underline instead of solid) and a tooltip/note explaining "likely Sanskrit transliteration"
- Does **not** suppress the error — user still sees it, just with context

**Out of scope:** Auto-accepting Sanskrit during spellcheck. Configuring the threshold per user.

**Acceptance criteria:**
- [ ] API response includes the new fields for every error
- [ ] UI renders likely-Sanskrit errors visually distinct from regular errors
- [ ] Existing spellcheck tests updated and passing; new test asserts the field is present
- [ ] Pure-Tibetan misspellings still surface as normal errors (no false suppression)

**Dependencies:** T-02

---

### T-03 — Page quality scorer

**Deploy:** `prod`
**Why:** Drives the accept/retry/reject decision. Phase-1-only for now since the corpus is empty; designed to accept Phase 2 weight later.

**Scope:**
- New module: `backend/app/ocr_assist/quality.py`
- `score_page(ocr_text, spellcheck_result, ocr_diagnostics) -> PageQuality`
- `PageQuality` includes: `non_tibetan_char_ratio`, `structural_error_ratio`, `sanskrit_adjusted_error_ratio`, `line_count_sanity`, `encoding_error_count`, `composite_score`, `breakdown` (dict of named contributions for UI display)
- Composite formula documented in module docstring; weights configurable via constants at top of file
- `decide(quality: PageQuality, thresholds: Thresholds) -> Literal["accept", "escalate", "reject"]`

**Out of scope:** Threshold tuning (T-10). Phase 2 corpus weight (later, when corpus is populated).

**Acceptance criteria:**
- [x] Module + functions exist with documented composite formula
- [x] Uses T-02's Sanskrit scorer to compute `sanskrit_adjusted_error_ratio`
- [x] Phase 2 inputs are present in the function signature but weighted at 0 for now, with a TODO marker
- [x] Unit tests with hand-crafted inputs covering each branch of `decide`

**Dependencies:** T-02

---

### T-04 — Filesystem job store + per-page settings model

**Deploy:** `local-only`
**Why:** The state model is the foundation everything else builds on. Doing this before the loop means the loop has somewhere to write.

**Scope:**
- New module: `backend/app/ocr_assist/job_store.py`
- `Job` dataclass: `id`, `source_file`, `baseline_settings`, `created_at`, `page_count`, `status`
- `PageState` dataclass: `index`, `image_path`, `settings`, `attempts: list[AttemptRecord]`, `final_text`, `final_quality`, `notes`
- Directory layout as documented in the Per-page state model section
- Functions: `create_job`, `load_job`, `save_page_attempt`, `finalize_page`, `list_jobs`
- Atomic writes (write-temp-then-rename) for JSON files so a crash mid-write doesn't corrupt state

**Out of scope:** OCR execution (T-05). UI exposure (T-08).

**Acceptance criteria:**
- [x] Creating a job from a PDF persists `manifest.json` + `baseline_settings.json` + one directory per page with `image.png`
- [x] `save_page_attempt` writes under `attempts/NN/` with monotonic numbering
- [x] `finalize_page` writes `final.txt` and `final_quality.json`
- [x] `load_job` round-trips a previously saved job
- [x] Tests cover create, save attempt, finalize, reload

**Dependencies:** none (can run alongside T-01/T-02/T-03)

---

### T-05 — Per-page OCR runner with retry loop (no AI yet)

**Deploy:** `local-only`  
**Status:** ✅ Done (superseded in part by T-05b, T-06, T-07 — runner now supports full loop)

**Why:** Get the control flow working before adding the API dependency. With no AI verdicts available, retries are skipped and pages either accept or go straight to human-review queue.

**Scope:**
- New module: `backend/app/ocr_assist/runner.py`
- `run_page(job, page_index, diagnostician=None, vision_transcriber=None) -> RunResult`
- When `diagnostician is None`, no retries — accept or escalate-to-human only (vision fallback optional via T-07)
- Wires together: OCR (`backend/app/pdf/ocr.py`), spellcheck, T-03 quality scorer, T-04 job store
- CLI: `python -m app.ocr_assist.run_job <pdf_path>` (`--enable-ai` added in T-07b)

**Out of scope:** LLM integration (T-06, T-07). Per-page settings reaching BDRC (T-05b). UI (T-09).

**Acceptance criteria:**
- [x] Can run end-to-end on a small PDF, producing a populated job directory
- [x] Pages with high score auto-accept; low-score pages have status `needs_review`
- [x] No retries happen when `diagnostician is None`
- [x] Existing spellcheck tests still pass

**Dependencies:** T-03, T-04

---

### T-05b — Per-page BDRC settings plumbing

**Deploy:** `prod` (local computation; makes T-06 retries meaningful)  
**Status:** ✅ Done

**Why:** T-06 persisted diagnostician setting overrides to `settings.json`, but the OCR adapter ignored them — every retry produced identical BDRC output. This ticket wires `settings.json` → `BDRCOCREngine.run_on_image` → `OCRPipeline.run_ocr(k_factor, bbox_tolerance, model_variant, rotate)`.

**Scope:**
- `backend/app/pdf/ocr_settings.py` — parse page settings, map diagnostician aliases (`Ume` → `Ume_Druma`) to OCR model dirs
- `backend/app/pdf/ocr.py` — accept `page_settings`, swap ONNX models via `update_ocr_model()`, apply manual rotation
- `runner._default_ocr_adapter` — forward `page.settings` to the engine

**Acceptance criteria:**
- [x] `k_factor` / `bbox_tolerance` overrides change `run_ocr` parameters
- [x] `model_variant` override loads and activates the correct OCRModels directory
- [x] `rotate` applied before OCR (clockwise per diagnostician convention)
- [x] Unit tests in `tests/test_ocr_settings.py`

**Dependencies:** T-05

---

### T-06 — LLM quality diagnostician

**Deploy:** `behind-flag` (local-only until auth + admin flag exist)  
**Status:** ✅ Done — 2 live-API smoke tests pending (see acceptance criteria)

**Why:** The retry decision-maker. Sees the image + OCR + quality breakdown and decides what to try next.

**Scope:**
- Implementation: `backend/app/ocr_assist/providers/anthropic_diagnostician.py` (re-exported from `diagnostician.py`)
- Reads `ANTHROPIC_API_KEY` from env
- Verdict union: `RetryWithSettings`, `AccurateAsSanskrit`, `NeedsHuman`
- Structured output via Anthropic tool use; prompt caching on system prompt + tools + page image
- Plugged into `run_page` as the `diagnostician` argument
- Cap retries at `max_attempts` (default 3)

**Out of scope:** Vision-OCR fallback (T-07). Provider abstraction (T-07b). Error resilience (T-12).

**Acceptance criteria:**
- [x] Module exists and is callable with a real API key
- [x] Verdicts deserialize into the typed union; malformed responses raise `DiagnosticianError`
- [x] `run_page` with diagnostician wired in produces retry attempts on a deliberately-bad page
- [ ] Sanskrit-heavy page produces `AccurateAsSanskrit` verdict (manual smoke — [INTERACTIVE_OCR_LOCAL_SMOKE.md](INTERACTIVE_OCR_LOCAL_SMOKE.md) Phase C)
- [ ] System prompt cached (verify `cache_read` tokens > 0 on second call same page — Phase B)

**Dependencies:** T-05, T-05b

---

### T-07 — Vision-OCR fallback

**Deploy:** `behind-flag` (local-only until auth + admin flag exist)  
**Status:** ✅ Done — 1 live-API smoke test pending

**Why:** For pages where BDRC retries don't converge, give a vision model a chance to read the image directly.

**Scope:**
- `backend/app/ocr_assist/providers/anthropic_vision.py` (re-exported as `VisionOcr`)
- Triggered by `run_page` when a page would otherwise be `needs_review` (attempts exhausted or diagnostician `needs_human`)
- Vision transcript scored with same quality scorer; accept → finalize with provenance note; else persist `vision_ocr.json` + `vision_quality.json`
- Strict transcription prompt (no normalize/correct)

**Out of scope:** Diff/merge UI. Gemini provider (T-07b). Mixed-script skip logic (T-11).

**Acceptance criteria:**
- [ ] Known-bad page produces a vision transcript (live API — [INTERACTIVE_OCR_LOCAL_SMOKE.md](INTERACTIVE_OCR_LOCAL_SMOKE.md) Phase B)
- [x] Vision transcript scored and either accepted or attached to human-review record
- [x] No vision call on pages that accept on first BDRC attempt

**Dependencies:** T-06

---

### T-07b — LLM provider abstraction

**Deploy:** `behind-flag`  
**Status:** ✅ Done

**Why:** Swap vision provider (Claude vs Gemini) without touching runner logic; share contracts and Anthropic helpers; prepare for future diagnostician providers.

**Scope:**
- `backend/app/ocr_assist/contracts.py` — `VisionTranscript`, verdict types, `DiagnosticianCallable`, `VisionTranscriberCallable`
- `backend/app/ocr_assist/providers/` — Anthropic diagnostician + vision, Gemini vision, factories
- Runner params renamed: `diagnostician`, `vision_transcriber` (was `claude_*`)
- CLI: `--enable-ai`, `--diagnostician-provider`, `--vision-provider`
- Env vars documented in `.env.example`

**Out of scope:** Gemini in requirements.txt (httpx conflict — T-15). Diagnostician on Gemini.

**Acceptance criteria:**
- [x] `build_diagnostician()` / `build_vision_transcriber()` construct provider implementations
- [x] `VISION_OCR_PROVIDER=gemini` works when `google-genai` installed + `GEMINI_API_KEY` set
- [x] Existing diagnostician/vision/runner unit tests pass via compatibility shims

**Dependencies:** T-06, T-07

---

### T-08 — Clean DOCX export with page numbers

**Deploy:** `prod`
**Why:** The final artifact the user actually wants.

**Scope:**
- Extend `backend/app/pdf/docx_exporter.py` (or add a sibling module) with a "clean export" mode mirroring `tibetan-ocr-app/BDRC/Exporter.py:DocxExporter`:
  - `Page N` heading per page (Heading 2 style)
  - Tibetan Machine Uni 14pt body
- Write incrementally as pages are finalized in the job store (page accepted → appended to `output.docx`)
- Existing spell-check-highlighted DOCX mode stays available as a separate option

**Out of scope:** Wylie output (the upstream exporter supports it but not needed for this workflow).

**Acceptance criteria:**
- [ ] Finalizing a page in the job store appends a `Page N` section to `output.docx`
- [ ] Resume after crash: re-finalizing already-written pages doesn't duplicate them (use page index to dedupe)
- [ ] Output opens cleanly in Word and Pages and renders Tibetan correctly when the font is installed

**Dependencies:** T-04

---

### T-09 — Interactive review UI

**Deploy:** `local-only` initially; once auth lands, the AI-using parts become `behind-flag`
**Why:** The human-in-the-loop surface for pages that exhaust retries.

**Scope:**
- New Next.js page: `frontend/pages/ocr-interactive.tsx`
- Upload a PDF → creates a job → progresses through pages
- Live updates as pages auto-accept (auto-advance) or stall
- For stalled pages: side-by-side image + current OCR text + quality breakdown + iteration log (each attempt with settings, score, AI verdict)
- Human actions: accept, edit text, skip, change model variant, manually tweak settings + retry
- Backend endpoints: `POST /api/ocr-job`, `GET /api/ocr-job/:id`, `GET /api/ocr-job/:id/page/:n`, `POST /api/ocr-job/:id/page/:n/action`

**Out of scope:** Multi-user, auth, job history list (just show the current job).

**Acceptance criteria:**
- [ ] Can upload a PDF and watch pages flow through the loop
- [ ] Stalled pages show the full iteration log
- [ ] Each human action updates the job store and either re-runs the page or advances
- [ ] DOCX is downloadable when all pages are finalized

**Dependencies:** T-05 (minimum); T-06 and T-07 to be useful; T-08 for the final download

---

### T-10 — Threshold calibration on real pages

**Deploy:** `local-only` (one-off exercise; resulting thresholds get committed to code)  
**Status:** ⬜ Not started

**Why:** The composite-score thresholds in T-03 are guesses until calibrated against pages from the actual target text.

**Scope:**
- Run the pipeline against the user's specific target PDF
- Collect per-page scores + human accept/reject decisions
- Tune accept/reject thresholds and per-signal weights to minimize false-accept and false-reject rates
- Document chosen thresholds in `docs/planning/INTERACTIVE_OCR_CALIBRATION.md`
- Incorporate bilingual page labels from T-16 / T-11 smoke notes

**Out of scope:** Automated calibration (manual is fine for one text).

**Acceptance criteria:**
- [ ] Thresholds documented with sample size and false-accept/false-reject counts
- [ ] On the calibration set, < ~5% of accepted pages later turn out to be bad on human review (target — adjust after data)

**Dependencies:** T-05 minimum (CLI + job store). T-09 UI helpful but not required — filesystem inspection + [INTERACTIVE_OCR_LOCAL_SMOKE.md](INTERACTIVE_OCR_LOCAL_SMOKE.md) suffices. T-11 should land before or alongside calibration if bilingual pages are in the target text.

---

### T-11 — Mixed-script guardrails (English + Tibetan)

**Deploy:** `prod` (local computation — reduces API waste)  
**Status:** ⬜ Not started

**Why:** Legitimate English on bilingual pages can trigger diagnostician retries and vision calls even when BDRC got the Tibetan right, because `non_tibetan_char_ratio` treats all Latin like OCR garbage. See [INTERACTIVE_OCR_MIXED_SCRIPT.md](INTERACTIVE_OCR_MIXED_SCRIPT.md).

**Scope (layer 1 — ship first):**
- `tibetan_only_composite_score` on `PageQuality` (score `extract_tibetan(ocr_text)` separately)
- Runner/diagnostician preflight: if `non_tibetan_char_ratio >= threshold` and Tibetan-only score clears `accept`, auto-accept and skip LLM calls
- Optional job baseline flag: `expect_mixed_script: true`

**Scope (layer 2 — optional follow-up):**
- Latin block vs scattered-Latin detection to distinguish intentional English paragraphs from OCR noise

**Acceptance criteria:**
- [ ] Bilingual fixture (clean Tibetan + English blocks) auto-accepts without diagnostician
- [ ] Scattered-Latin garbage fixture still escalates
- [ ] Thresholds documented alongside T-10 calibration

**Dependencies:** T-03, T-05. Best calibrated with T-10/T-16 data.

---

### T-12 — Provider error resilience

**Deploy:** `behind-flag`  
**Status:** ⬜ Not started

**Why:** `DiagnosticianError`, `VisionTranscriberError`, and vendor API failures currently crash `run_page` instead of falling back to `needs_review`.

**Scope:**
- Wrap diagnostician and vision calls in `runner.py`
- On failure: log error, persist reason on page (notes or attempt metadata), return `needs_review` without killing `run_all_pages` batch
- Unit tests with raising stubs

**Acceptance criteria:**
- [ ] Malformed LLM response → page queued for review, batch continues
- [ ] Network/API auth error → same

**Dependencies:** T-06, T-07

---

### T-13 — Line-count sanity baseline

**Deploy:** `prod`  
**Status:** ⬜ Not started

**Why:** `line_count_sanity` is wired but inert — `expected_line_count` is never set, so the signal always returns 1.0.

**Scope:**
- Track rolling median line count from accepted pages in a job
- Pass `expected_line_count` into `OcrDiagnostics` for subsequent pages
- Optionally use deviation to weight retry decisions

**Acceptance criteria:**
- [ ] After 3+ accepted pages, a page with half the expected lines scores lower on line sanity
- [ ] First page of job unchanged (no baseline yet)

**Dependencies:** T-03, T-05

---

### T-14 — CLI ergonomics

**Deploy:** `local-only`  
**Status:** ⬜ Not started

**Why:** Local smoke and calibration need finer control than "run entire PDF."

**Scope:**
- `run_job` flags: `--max-attempts`, `--pages 3,7,12` (1-based subset)
- Re-run a single page: load existing job, clear `final.txt` + attempts for one page, resume
- Optional: `--threshold-accept` / `--threshold-reject` overrides for T-10 experiments

**Acceptance criteria:**
- [ ] Can re-OCR page 7 of an existing job without re-creating the job
- [ ] Page subset runs only listed pages (others untouched)

**Dependencies:** T-04, T-05

---

### T-15 — Gemini optional dependency (httpx conflict)

**Deploy:** `infrastructure`  
**Status:** ⬜ Not started

**Why:** `google-genai` requires `httpx>=0.28`; project pins `httpx==0.26.0` for FastAPI `TestClient` compatibility. Gemini works locally via manual install but isn't in `requirements.txt`.

**Scope:**
- Evaluate upgrading `fastapi` / `starlette` / `httpx` together, or document optional extra (`pip install -e ".[gemini]"`)
- Add Gemini to CI optional job once conflict resolved
- Update `.env.example` and provider factory error messages

**Acceptance criteria:**
- [ ] Documented install path that doesn't break `tests/test_api_spellcheck.py`
- [ ] CI green with or without Gemini installed

**Dependencies:** T-07b

---

### T-16 — Local smoke test + vision A/B

**Deploy:** `local-only` (process, not code)  
**Status:** 📋 Procedure documented — run after merge

**Why:** Tick remaining T-06/T-07 live-API acceptance criteria; pick default vision provider; feed T-10/T-11 calibration.

**Scope:**
- Follow [INTERACTIVE_OCR_LOCAL_SMOKE.md](INTERACTIVE_OCR_LOCAL_SMOKE.md) Phases A–E
- Record results in `docs/planning/INTERACTIVE_OCR_VISION_AB.md` (create during run)
- Flag bilingual pages that wasted retries → input for T-11

**Acceptance criteria:**
- [ ] Phase A (BDRC-only) on 5-page sample
- [ ] Phase B (full Claude loop) with API keys
- [ ] Phase D (Claude vs Gemini vision) on pages that triggered fallback
- [ ] T-06/T-07 unticked smoke criteria resolved or issues filed

**Dependencies:** T-07b merged; `ANTHROPIC_API_KEY` in `backend/.env`. Gemini optional.

---

## Future / not yet ticketed

- **Physical-book photos:** different baseline preset (perspective correction, glare detection, possibly different model variant). Architecturally accommodated by the per-page settings model.
- **Phase-2 corpus weight:** wire `unknown_word` rate back into the quality scorer once the corpus is populated. The hook is already in T-03's function signature.
- **Admin flag for AI features:** once auth exists, add `FEATURE_AI_OCR_ASSIST` env flag + admin role check at the API layer; gate T-06/T-07/T-09 routes accordingly. Include a server-side cost cap (max API calls per job, or daily spend cap) as defense-in-depth.
- **GitHub mirror:** if useful, sync these tickets to GH issues so you can comment/track status outside markdown.
- **Multi-text resume:** today the job store is single-tenant. Listing/switching jobs in the UI is a future concern.
- **Gemini diagnostician:** T-07b only abstracts vision; diagnostician remains Anthropic-only unless demand appears.
- **PREPARE integration:** style detection ([PREPARE_FEATURE.md](PREPARE_FEATURE.md)) could set `expect_mixed_script` on jobs with detected English Body styles — ties into T-11 long-term.

### Suggested order after merge

1. **T-16** — local smoke + vision A/B (validates what's built)
2. **T-11** — mixed-script guardrails (if smoke shows wasted retries on bilingual pages)
3. **T-12** — error resilience (before running full book)
4. **T-10** — threshold calibration on target PDF
5. **T-14** — CLI ergonomics (if re-running single pages gets tedious)
6. **T-08** → **T-09** — DOCX export then review UI
7. **T-02b**, **T-13**, **T-15** — as needed / parallel
