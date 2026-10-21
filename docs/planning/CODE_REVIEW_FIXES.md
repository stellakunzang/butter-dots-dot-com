# Code Review Fixes Plan

Findings from a full-repo review (backend security, frontend, file structure,
tests, dead code, docs, correctness/hygiene), grouped into independent
branches. Line numbers are as of the review and will drift.

The work is split into two tracks:

- **Track A — core (non-OCR-assist):** spellcheck, PDF pipeline, shared
  frontend, docs, CI, repo hygiene. Small, independent branches.
- **Track B — OCR assist, cut and retarget:** pull vision and the
  diagnostician retry loop, keep the page record and human proofing, and
  defer phone capture until a one-leaf still test. See Track B below. The
  old B1–B4 polish checklist is withdrawn.

Sizes: **S** < 1h, **M** half day, **L** a day or more.

---

## Step 0 — Separate the current uncommitted work

The working tree mixes both tracks:

- OCR assist: `runner.py`, `run_job.py`, `ocr-assist.tsx`, and
  `test_runner.py`, `test_run_job_cli.py`, `test_run_job_summary.py`,
  `test_api_ocr_assist.py`; untracked `scripts/ocr_ab_test.py`.
- Core: `README.md`, `.github/PULL_REQUEST_TEMPLATE.md`.

Move the OCR changes onto a parked branch before starting Track A, so core
branches start from a clean `main`. Do not fix the uncommitted runner resume
bugs first. They live in the retry loop Track B is removing, and that branch
is only a snapshot until the cut is done.

---

## Track A — Core

Suggested order: A1 → A2 → A3 → A4 → A5, then A6/A7 in any order.
A4 (CI) comes after A3 so new lint/type/test gates don't land red.

### A1. Security and dependencies — `fix/deps-and-upload-hardening`

Implemented on `fix/deps-and-upload-hardening`, not committed yet.

- [x] **S** `python-multipart==0.0.32` (CVE-2024-24762, CVE-2024-53981 fixed
      since 0.0.18) and `pypdf==6.21.1` (JPEG / content-stream advisories).
      Call sites are `PdfReader` / `PdfWriter` only.
- [x] **S** `pytest` moved to `requirements-dev.txt`. Dropped unused `alembic`,
      `regex`, and `pytest-asyncio`. Kept `psycopg2-binary`: SQLAlchemy uses it
      when `DATABASE_URL` is Postgres. CI installs `requirements-dev.txt`.
      The production Dockerfile still installs `requirements.txt` only.
- [x] **S** `backend/.dockerignore` and `frontend/.dockerignore`.
- [x] **S** Spellcheck errors returned to clients are generic. Exceptions are
      logged. `mark_failed` stores "PDF processing failed".
- [x] **M** Public uploads: 50 MB, read in chunks, `Content-Length` reject,
      `MAX_PAGES = 500`. OCR assist stays at 100 MB (local book scans) and now
      returns 413 like the public endpoint. Caps live in `app/upload_limits.py`.
- [x] **M** `extract_scanned` renders one page at a time.
- [x] **S** Optional email validated with `EmailStr` (blank is omitted, so the
      queue message no longer says "sent to None"). `%PDF-` magic-byte check.
      Download names stripped of header and path characters.
- [x] **S** Feedback route awaits Formspree, caps the body at 32 KB / 5000
      characters, rate-limits per IP, and ignores a filled `company` honeypot.

### A2. Repo hygiene — `chore/repo-cleanup`

- [ ] **S** Delete boilerplate/dead code: `frontend/pages/api/hello.ts`,
      `frontend/public/vercel.svg`, `frontend/components/CodeBlock.tsx` (+ its
      export in `components/index.ts:5`), `backend/BDRC/utils/`.
- [ ] **S** Move loose files out of `backend/`: `check_file.py` →
      `scripts/`; `sample_text.*`, `spellchecker_test.rtf`, `test_with_errors.*`
      → `tests/fixtures/` (or delete if unused); `MANUAL_TESTING.md` → `docs/`.
- [ ] **S** Check `backend/scripts/download_models.py` against the Dockerfile;
      delete or document.
- [ ] **S** Add `LICENSE` and a third-party notice (BDRC is MIT). Confirm
      whether any GPL code (Paul Hackett's spellchecker,
      `docs/research/SCRIPT_ANALYSIS.md:4`) was actually incorporated, and word
      that doc accurately.
- [ ] **S** Prune stale remote branches (36 remote). Never push
      `feat/lexicon-pipe-ingest` (third-party dictionary dumps).

### A3. Tests — `test/strengthen-assertions`

- [ ] **S** Fix the always-true assertion `backend/tests/test_validation.py:256`.
- [ ] **S** Remove vacuous `if result:` checks in `test_engine.py:78,103`;
      delete the weaker duplicate of `TestEncodingErrors`.
- [ ] **S** Remove commented-out assertions `test_engine.py:1019-1022`.
- [ ] **S** Unskip or delete `frontend/__tests__/pages/spellcheck.test.tsx:154,174`.
- [ ] **M** Investigate the 4 failing `test_ocr_parity.py[Tashi Gyedpa]` cases
      ("Genuine error count differs by 30"); confirm whether they run or skip in
      CI. Add `-rs` to pytest addopts so skips are visible.
- [ ] **M** Add backend upload tests: non-PDF with `.pdf` extension, oversized,
      empty, corrupt, path-traversal filename, 15 vs 16 page threshold; download
      and status endpoints for unknown / unfinished jobs.
- [ ] **M** Convert `test_validation.py:131-240` to a parametrized
      `(syllable, expected_error_type)` table; replace bare `is not None`
      asserts; module-scoped engine fixture in `test_engine.py`.
- [ ] **S** Check for overlap: `test_docx_export.py` vs `test_docx_exporter.py`,
      `test_dictionary.py` vs `test_engine_dictionary.py`.
- [ ] **S** Add `@types/jest` to frontend dev deps.

### A4. CI and tooling — `ci/lint-typecheck-build`

- [ ] **S** Add ruff (`pyproject.toml`, `ruff check` + `ruff format --check`),
      run once over `backend/app` and `backend/tests` (exclude `BDRC/`).
- [ ] **S** Add Prettier config; CI runs `yarn lint`, `tsc --noEmit`,
      `yarn build`.
- [ ] **S** `actions/setup-python@v4` → v5; `curl -fsS` for the deploy hook;
      remove the Postgres service if no test needs it.
- [ ] **M** Playwright job in CI. Rename `e2e/pdf-upload.spec.ts` to reflect
      that it mocks the API, or add one unmocked smoke test. Replace the
      `setTimeout(400)` at `:214` with a deferred promise.

### A5. Docs — `docs/readme-and-cleanup`

Do after A2 so links point at final paths. Coordinate the OCR sections of the
README with Track B.

- [ ] **S** Remove `docs/planning/INTERACTIVE_OCR_WORKFLOW.md` (AI-assistant
      workflow prompt) and its entry in `docs/README.md`.
- [ ] **M** Restructure `README.md` (~150 lines): pitch + screenshot, features,
      architecture diagram, key engineering decisions (link ADRs), quickstart,
      layout, docs index, acknowledgments. Move OCR CLI reference, deployment
      and troubleshooting into `docs/`. State that `backend/BDRC/` is vendored.
- [ ] **S** Fix broken links (`docs/guides/ARCHITECTURE.md` →
      `frontend/docs/ARCHITECTURE.md`; nonexistent archive entries; links
      wrapped in backticks) and step numbering (README ~64-79, 353).
- [ ] **S** Delete `ARCHITECTURE_SIMPLE.md`, `docs/archive/`,
      `docs/planning/BACKLOG.md`.
- [ ] **M** Trim `docs/adr/SPELLCHECKER_DECISIONS.md` to
      Context / Decision / Consequences per entry; drop status emoji.
- [ ] **S** Decide which remaining planning/research docs stay public
      (`LIVE_PECHA_CAPTURE`, `PREPARE_FEATURE`, `WORD_CORPUS_PLAN`,
      `EDUCATIONAL_CONTENT_PLAN`); trim or move.
- [ ] **S** Comment nits: `app/utils/email.py:20` TODO → documented limitation;
      `config.py:19-20` "Render/Railway"; restating comments at
      `completeness_checks.py:149`, `parser.py:179`.
- [ ] **S** Add "How tested" to `.github/PULL_REQUEST_TEMPLATE.md`.

### A6. Frontend shared code — `refactor/frontend-shared`

Shared frontend pieces for spellcheck and the rest of the app. The slimmed
OCR proofing page can adopt them when Track B happens; it does not have to
land first.

- [ ] **S** `lib/config.ts`: single `API_URL` (currently duplicated in
      `lib/api.ts:5` and `lib/ocrAssist.ts:8`) that fails loudly when unset in
      production.
- [ ] **M** `lib/http.ts`: shared `request<T>()` + `parseError`, replacing the
      inline copies in `lib/api.ts:47-83,152-179,186-194`.
- [ ] **S** Fix `components/JobStatus.tsx:17-45` polling: clear the timeout on
      unmount, hold `onCompleted` in a ref, surface `failed` status.
- [ ] **S** Replace `dangerouslySetInnerHTML` at `pages/spellcheck.tsx:277`.
- [ ] **M** Shared UI primitives: `Alert`, `Spinner`, icons module; use
      existing `Button`/`TabButton`; replace `colorClass` prop on
      `PDFDownloadLink` with a variant.
- [ ] **L** Learn pages: move tables/examples into typed content
      (`content/learn/*.ts`), shared `components/learn/*`.

### A7. Backend robustness — `fix/job-store-and-engine`

Note: `app/pdf/ocr.py` (BDRC engine) is shared by the public PDF spellcheck
path and OCR assist, so its fixes live here, not in Track B.

- [ ] **S** Lock around lazy `_load` and `update_ocr_model` in the shared
      `BDRCOCREngine` (`app/pdf/ocr.py:66-248`).
- [ ] **M** `app/jobs.py`: lock around `_jobs`, TTL sweep for jobs and
      `results/` files; document the single-instance constraint.
- [ ] **S** `spellcheck.py:236-245`: email failure must not mark a completed
      job as failed.
- [ ] **M** Move import-time side effects (`spellcheck.py:32-36`,
      `corpus.py:12`) into FastAPI lifespan / dependencies.
- [ ] **M** Migration `002_lexicon_schema.sql:88-99`: untargeted
      `ON CONFLICT DO NOTHING`, rename instead of `DROP`, keep `source_count`.
      Decide on unused `jobs` / `spell_errors` tables in `schema.sql`.
- [ ] **S** Docker/deploy: non-root user, `HEALTHCHECK`, exec-form `CMD`,
      `healthCheckPath: /api/v1/health` in `render.yaml`, drop obsolete compose
      `version:`, bind Postgres to `127.0.0.1`.

---

## Track B — OCR assist, cut and retarget

One branch, after Track A is underway or done. The old B1–B4 polish list is
withdrawn: it assumed we would keep the auto-accept loop, the diagnostician,
and vision compare, then refactor that UI.

Agreed shape: a page image, one BDRC read, a human looking at the image and
the text, then a DOCX. A bad frame is fixed by another photo, or by a model
and rotation the human picks. The composite score does not auto-accept. Hard
floors (near-empty, repetition, suspiciously short) stay as retake hints.

Phone capture is not this branch. It waits on the one-leaf spike in B3.

### B0. Record — diagnostician

Keep this recoverable by reference. Do not leave the modules in tree, and do
not copy them into an archive directory.

- Introducing PR:
  [#57](https://github.com/stellakunzang/butter-dots-dot-com/pull/57) —
  `[T-06] Add Claude-backed OCR diagnostician with retry loop` (merged
  2026-06-09). Below the accept threshold the runner sent Claude the page
  image, OCR text, quality breakdown, and prior attempts. Claude returned one
  of `RetryWithSettings`, `AccurateAsSanskrit`, or `NeedsHuman`, capped at
  `max_attempts` (default 3).
- That PR is the original add. The files moved after it. The snapshot to
  resurrect is the parent of the deletion commit, not the #57 diff alone.
  Follow-ups that changed the loop:
  [#60](https://github.com/stellakunzang/butter-dots-dot-com/pull/60)
  (vision and the provider split),
  [#67](https://github.com/stellakunzang/butter-dots-dot-com/pull/67)
  (foundation landing),
  [#70](https://github.com/stellakunzang/butter-dots-dot-com/pull/70)
  (intervention log and retry flags).
- Anchor files on the deletion parent: `backend/app/ocr_assist/diagnostician.py`,
  `providers/anthropic_diagnostician.py`, verdict types in `contracts.py`, and
  the diagnostician branch of `run_page` in `runner.py`.
- Vision does not get its own archive. It arrived in #60 and leaves with this
  cut. Git history is enough. Say that in the deletion commit message, and
  point the message at #57 for the diagnostician.

### B1. Remove — `refactor/ocr-assist-cut`

- [ ] **L** Delete the vision path: `vision_ocr.py`, `compare_vision.py`,
      `providers/anthropic_vision.py`, `providers/gemini_vision.py`, vision
      helpers on the job store, and the compare/vision API routes and UI.
- [ ] **M** Delete the diagnostician call path from `runner.py`, `run_job.py`,
      and the API. Remove `diagnostician.py` and
      `providers/anthropic_diagnostician.py` after B0 is cited in the commit
      message.
- [ ] **L** Slim `pages/ocr-assist.tsx` to image, text, rotate, edit, accept,
      a human-chosen model or rotation retry, and DOCX export. Drop the vision
      model select and AI compare panel. Do not first split the page into the
      old component map (`VisionModelSelect`, `AiComparePanel`, and the rest).
- [ ] **M** Delete tests that only cover vision compare and diagnostician
      verdicts. Keep job store, DOCX, BDRC run-once, and quality hard-floor
      coverage. Drop `--vision` from `scripts/ocr_ab_test.py`; leave the BDRC
      model comparison.
- [ ] **S** Generic errors, bounded `text` / `rotate` on page actions, and the
      production gate (`OCR_ASSIST_LOCAL` plus a frontend 404) stay. They apply
      to the slimmed proofing page.

### B2. Keep, without a structural refactor

Leave these in place. A later capture feature should write into them.

- Job store page model: `image.png`, attempts, `final.txt`, per-page settings.
  A PDF render and a future camera still both land in `image.png`.
- BDRC adapter and model variants (Woodblock, Ume, and the rest).
- `quality.py` hard floors, surfaced as hints. No auto-finalize on the
  composite score.
- Sanskrit adjustment inside the scorer.
- Clean DOCX export.
- Proofing actions: accept, edit, rotate, retry with a chosen model.

Revisit a bug from the old list only when the slimmed page still has it:
image path bounds, corrupt-PDF job cleanup, attempt sort past 99, a failed
page status, and polling that dies after one failed fetch. Skip the rest.
They belonged to vision compare or the diagnostician retry loop.

### B3. Later — one-leaf camera spike

Not this cleanup. `docs/planning/LIVE_PECHA_CAPTURE.md` is still an empty
checklist. Do not build a capture UI first.

1. A few Continuity Camera stills of one pecha leaf, run through the BDRC
   models, judged by eye. The question is whether a phone photo is readable.
2. If the read is usable: image ingest (still → `image.png`), then a fast
   blur/framing check, then a small capture UI.
3. If the still is not readable: preprocess (crop, deskew, perspective)
   before any new interface.

### Docs in this pass

- [ ] **S** Add a short status note at the top of
      `docs/planning/INTERACTIVE_OCR_PLAN.md` pointing here. Leave that plan
      as history.
- [ ] **S** When A5 rewrites the README, describe this as local proofing:
      image, BDRC text, human accept, DOCX. Drop vision fallback from the pitch.

---

## Deliberately not doing

- Pruning unused functions in vendored `backend/BDRC/` — keeps upstream syncs
  clean. Documenting it as vendored (A5) is enough.
- Rewriting git history for `9277273` (removed a committed `.next/` cache; no
  secrets involved).
- Splitting `quality.py`, `parser.py`, `job_store.py`, `build_corpus.py` — long
  but cohesive.
- Refactoring `/ocr-assist` into the withdrawn B3 component split, or fixing
  correctness bugs that only exist for vision compare and the diagnostician
  retry loop.
- Copying the diagnostician into an in-repo archive. PR #57 plus the deletion
  commit's parent is the record.
