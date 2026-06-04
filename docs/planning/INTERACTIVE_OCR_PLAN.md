# Interactive Page-by-Page OCR with AI Assistance

**Status:** Plan — not yet implemented.
**Goal:** Convert a Tibetan text into a Word document, one page at a time, where pages that come out clean auto-advance and pages that don't get an AI-assisted retry loop and (if still bad) surface to a human. No more global-tweak-that-breaks-other-pages.
**Scope:** Local-only for now. Single-user workflow. Future use case: photos of physical books (not yet in scope but shouldn't be architecturally blocked).

---

## Deployment posture

Anything that calls the Claude API must **not** run in production yet — unbounded per-page costs against an unmetered surface is exactly the failure mode we're avoiding. But several tickets are valuable on their own and safe to ship.

Each ticket below carries one of three tags:

- **`deploy: prod`** — pure local computation, no API cost, improves existing functionality. Safe to ship behind the normal merge flow.
- **`deploy: local-only`** — workflow/state that's only intended for local use right now. The code can live in `main` (it doesn't hurt anything sitting there), but the entry points stay off in prod via env flag or simply by not exposing routes.
- **`deploy: behind-flag`** — anything that calls the Claude API. Stays local-only until auth lands; then gated by an admin-only flag (e.g., `FEATURE_AI_OCR_ASSIST=true` + admin role check). Even after gating, consider a per-job cost cap.

When auth exists, the plan is: one feature flag (`ai_ocr_assist`) checked at the API layer, restricted to admin users. UI surfaces hide the AI controls when the flag is off. Cost cap (e.g., max-N-API-calls-per-job, or max-spend-per-day) enforced server-side regardless of role.

### What can ship to prod right now

- **T-01** — OCR engine improvements (strict upgrade)
- **T-02** — Sanskrit detector (new local module, no integration)
- **T-02b** — Surface Sanskrit signal in existing spellcheck API/UI (useful to spellcheck users today)
- **T-03** — Page quality scorer (local module; even if the AI loop isn't deployed, the scorer could power a "page quality" indicator in the existing spellcheck flow if useful)
- **T-08** — Clean DOCX export with page numbers (extends existing exporter; useful independent of the AI loop)

### What stays local-only / behind-flag

- **T-04, T-05** — Job store and runner: technically API-free but the interactive workflow isn't ready for prod users
- **T-06, T-07** — Claude diagnostician and vision fallback: API cost — gated
- **T-09** — Interactive UI: routes hidden in prod until auth + flag exist
- **T-10** — Calibration: a one-off local exercise

---

## Background

Two existing projects supply the parts:

- **`butter-dots-dot-com`** (this repo): FastAPI + Next.js. Already has the BDRC OCR pipeline vendored at `backend/BDRC/`, a Phase-1/Phase-2 spell-check engine at `backend/app/spellcheck/`, and a DOCX exporter at `backend/app/pdf/docx_exporter.py` that highlights spell-check errors. No Claude integration.
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
ask Claude: { image, ocr_text, quality breakdown, prior attempts }
  Claude verdict ∈ {
    "retry_with_settings": { k_factor, rotate, crop, model_variant, ... },
    "use_this_transcript": "...",          // vision-OCR fallback
    "accurate_as_sanskrit_accept",         // stops the loop cleanly
    "needs_human": "<reason>"
  }
  ↓
apply verdict, loop
  ↓ no (attempts exhausted)
surface to human with: image, current OCR, quality breakdown, Claude's notes
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

Two thresholds: `accept` (no AI) and `reject` (escalate). Pages in between queue for human review at the end. Thresholds are calibrated against real pages (see T-09).

### Sanskrit handling

**Local detector** (T-02): a pattern-based classifier that runs against each Phase-1-flagged syllable. Looks for:
- Telltale codepoints: ཾ (U+0F7E anusvara), ཿ (U+0F7F visarga), ྂ, ྃ
- Subjoined consonants in non-Tibetan combinations (e.g., subjoined ya/ra/la/va patterns that violate Tibetan stacking)
- Three-consonant stacks
- **Clustering bonus**: Sanskrit usually runs in contiguous blocks. If neighboring syllables are also flagged Sanskrit-like, increase confidence.

Output: per-syllable `sanskrit_likelihood ∈ [0, 1]`. The quality scorer uses this to compute `sanskrit_adjusted_error_ratio`.

**Claude tiebreaker** (T-06): when the AI diagnostician is consulted, one of its allowed verdicts is `accurate_as_sanskrit_accept`. This stops the retry loop without forcing a transcription rewrite.

### AI role

Claude plays two distinct roles, both invoked only when the local quality score is below `accept`:

1. **Quality diagnostician** — given the image + OCR text + quality breakdown + prior attempts, returns one of the verdicts in the loop diagram. Most useful for: detecting skew/multi-column, recommending a different model variant (Modern vs Woodblock vs Ume), confirming Sanskrit content.
2. **Vision-OCR fallback** — when retries don't converge, Claude reads the image directly. Not expected to beat BDRC on clean pages; expected to help on pathological pages (warped, mixed scripts, faded ink, future physical-book photos).

Both run against the Claude API using the user's existing account.

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

## Open questions to revisit before T-04

1. **Model variant selection.** Baseline starts on Modern, but should Claude be allowed to switch to Woodblock/Ume per page? My current lean: yes, it's a per-page setting like any other.
2. **Vision fallback trigger.** Automatic after N failed retries, or opt-in per page? Lean: automatic; cost is bounded.
3. **GitHub mirror.** Markdown-only here, or also push tickets to GH issues? Lean: markdown-first, mirror later if desired.

---

## Tickets

Each ticket below is sized to be a single PR. Dependencies are noted. The order is the suggested implementation order but T-01 and T-02 can run in parallel.

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

**Out of scope:** Threshold tuning (T-09). Phase 2 corpus weight (later, when corpus is populated).

**Acceptance criteria:**
- [ ] Module + functions exist with documented composite formula
- [ ] Uses T-02's Sanskrit scorer to compute `sanskrit_adjusted_error_ratio`
- [ ] Phase 2 inputs are present in the function signature but weighted at 0 for now, with a TODO marker
- [ ] Unit tests with hand-crafted inputs covering each branch of `decide`

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
**Why:** Get the control flow working before adding the API dependency. With no AI verdicts available, retries are skipped and pages either accept or go straight to human-review queue.

**Scope:**
- New module: `backend/app/ocr_assist/runner.py`
- `run_page(job, page_index, claude_diagnostician=None) -> PageState`: executes OCR with current settings, scores, accepts or queues for review
- When `claude_diagnostician is None`, no retries — accept or escalate-to-human only
- Wires together: existing OCR (`backend/app/pdf/ocr.py`), spellcheck engine, T-02 Sanskrit scorer, T-03 quality scorer, T-04 job store
- CLI entry point: `python -m backend.app.ocr_assist.run_job <pdf_path>` for testing without UI

**Out of scope:** Claude integration (T-06). Vision fallback (T-07). UI (T-08).

**Acceptance criteria:**
- [ ] Can run end-to-end on a small PDF, producing a populated job directory
- [ ] Pages with high score auto-accept; low-score pages have status `needs_review`
- [ ] No retries happen when `claude_diagnostician is None`
- [ ] Existing spellcheck tests still pass

**Dependencies:** T-03, T-04

---

### T-06 — Claude quality diagnostician

**Deploy:** `behind-flag` (local-only until auth + admin flag exist)
**Why:** The retry decision-maker. Sees the image + OCR + quality breakdown and decides what to try next.

**Scope:**
- New module: `backend/app/ocr_assist/diagnostician.py`
- Reads `ANTHROPIC_API_KEY` from env
- Function `diagnose(image_bytes, ocr_text, quality: PageQuality, prior_attempts: list[AttemptRecord]) -> Verdict`
- `Verdict` is a discriminated union:
  - `RetryWithSettings(settings_overrides: dict, rationale: str)`
  - `UseTranscript(text: str, rationale: str)` — but actual vision-OCR is T-07; for now the diagnostician should *not* return this verdict
  - `AccurateAsSanskrit(rationale: str)`
  - `NeedsHuman(reason: str)`
- Prompt enforces JSON output with a strict schema; uses prompt caching for the system prompt and tools spec
- Plug into `run_page` from T-05 as the `claude_diagnostician` argument
- Cap retries at `max_attempts` (default 3) regardless of verdicts

**Out of scope:** Vision-OCR fallback (T-07).

**Acceptance criteria:**
- [ ] Module exists and is callable with a real API key
- [ ] Verdicts deserialize into the typed union; malformed responses raise a clear error
- [ ] `run_page` with diagnostician wired in produces retry attempts on a deliberately-bad page
- [ ] Sanskrit-heavy page produces `AccurateAsSanskrit` verdict (manual smoke test, no need to mock)
- [ ] System prompt is cached (verify cache_read tokens > 0 on the second call in the same session)

**Dependencies:** T-05

---

### T-07 — Claude vision-OCR fallback

**Deploy:** `behind-flag` (local-only until auth + admin flag exist)
**Why:** For pages where retries don't converge, give Claude a chance to read the image directly.

**Scope:**
- Extend `diagnostician.py` (or add `vision_ocr.py`) with a separate call that asks Claude to transcribe the page
- Triggered automatically by `run_page` after `max_attempts - 1` failed retries, before declaring `needs_human`
- The vision-OCR result is scored using the same quality scorer; if it passes `accept`, it's used; if not, page goes to human review with both BDRC and Claude transcripts attached
- Strict prompt: "Transcribe the Tibetan text exactly as written. Do not correct, normalize, or interpret. Use Unicode."

**Out of scope:** Diff/merge UI between BDRC and Claude transcripts (could be a future ticket if useful).

**Acceptance criteria:**
- [ ] On a known-bad page that BDRC can't read, Claude vision produces a transcript
- [ ] Vision transcript is scored and either accepted or attached to the human-review record
- [ ] No vision call is made on pages that already accept on first OCR attempt

**Dependencies:** T-06

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
**Why:** The composite-score thresholds in T-03 are guesses until calibrated against pages from the actual target text.

**Scope:**
- Run the pipeline against the user's specific target PDF
- Collect per-page scores + human accept/reject decisions
- Tune accept/reject thresholds and per-signal weights to minimize false-accept and false-reject rates
- Document the chosen thresholds and the page set they were tuned on in `docs/planning/INTERACTIVE_OCR_CALIBRATION.md`

**Out of scope:** Automated calibration (manual is fine for one text).

**Acceptance criteria:**
- [ ] Thresholds documented with sample size and false-accept/false-reject counts
- [ ] On the calibration set, < ~5% of accepted pages later turn out to be bad on human review (target — adjust after data)

**Dependencies:** T-09 (need the UI to collect human decisions efficiently)

---

## Future / not yet ticketed

- **Physical-book photos:** different baseline preset (perspective correction, glare detection, possibly different model variant). Architecturally accommodated by the per-page settings model.
- **Phase-2 corpus weight:** wire `unknown_word` rate back into the quality scorer once the corpus is populated. The hook is already in T-03's function signature.
- **Admin flag for AI features:** once auth exists, add `FEATURE_AI_OCR_ASSIST` env flag + admin role check at the API layer; gate T-06/T-07/T-09 routes accordingly. Include a server-side cost cap (max API calls per job, or daily spend cap) as defense-in-depth.
- **GitHub mirror:** if useful, sync these tickets to GH issues so you can comment/track status outside markdown.
- **Multi-text resume:** today the job store is single-tenant. Listing/switching jobs in the UI is a future concern.
