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

- [x] **S** Deleted `frontend/pages/api/hello.ts`, `frontend/public/vercel.svg`,
      `frontend/components/CodeBlock.tsx` (and its export), and
      `backend/BDRC/utils/` (nothing imported it).
- [x] **S** `check_file.py` → `backend/scripts/` (import path updated).
      Sample texts → `backend/tests/fixtures/`. `MANUAL_TESTING.md` → `docs/`.
- [x] **S** `download_models.py` matches the Dockerfile `RUN` and now says so.
      Kept.
- [x] **S** `THIRD_PARTY_NOTICES.md` records BDRC as MIT. No project `LICENSE`:
      `stacking.py` says a rule table was derived from Hackett's GPL v3 VBA,
      and that source is not in the tree. `SCRIPT_ANALYSIS.md` no longer says
      the GPL material can be relicensed.
- [ ] **S** Prune stale remote branches. Not done here — deleting remotes
      needs an explicit list. Do not push `feat/lexicon-pipe-ingest`.

### A3. Tests — `test/strengthen-assertions`

- [x] **S** The always-true `or syllable` assertion now expects
      `unusual_mark_position`.
- [x] **S** Removed the vacuous superscript check (`རང` is valid) and the
      weaker encoding check. `TestEncodingErrors` already asserts the same
      codepoint.
- [x] **S** Removed the commented-out assertions in `test_readme_example`.
- [x] **S** Unskipped the two spellcheck page tests. They assert the inline
      error message; the page has no "Error" heading.
- [x] **M** Tashi Gyedpa parity: 4 cases fail locally when OCR models are
      present (genuine error count differs by 30; tolerance is 10). CI runs
      `pytest` with no models downloaded, and those fixtures skip via
      `_ocr_available()`. They are also `@pytest.mark.slow`, so
      `pytest -m "not slow"` skips them too. Tolerance was not raised.
      Follow-up is a separate branch, planned in
      [OCR_PARITY_BASELINE.md](OCR_PARITY_BASELINE.md). Do not fix it here.
- [x] **M** Upload tests cover non-PDF bytes, oversize, empty, unreadable,
      path-traversal filename, 15 vs 16 pages, and unknown / unfinished
      downloads.
- [x] **M** Impossible-syllable cases are one `(syllable, error_type)` table
      with a module-scoped engine. `test_engine.py` still builds an engine per
      test; construction is cheap and a file-wide signature change is not
      worth it.
- [x] **S** No overlap to merge: `test_docx_export.py` is the clean OCR DOCX,
      `test_docx_exporter.py` is the spellcheck-annotated DOCX.
      `test_dictionary.py` is the dictionary service; `test_engine_dictionary.py`
      is the engine's use of it.
- [x] **S** `@types/jest@29` (matches Jest 29).

### A4. CI and tooling — `ci/lint-typecheck-build`

- [x] **S** Ruff in `backend/pyproject.toml` (`ruff check` + `ruff format --check`)
      over `backend/app` and `backend/tests`. `BDRC/` excluded. Quote style
      preserved. CI runs both.
- [x] **S** Prettier config and `format` / `format:check` scripts. CI runs
      `yarn lint`, `yarn tsc --noEmit`, and `yarn build`. Format is not a CI
      gate yet — the tree has not been formatted.
- [x] **S** `actions/setup-python@v5`. Deploy hook uses `curl -fsS`. Postgres
      service removed: no test connects. `test_dictionary.py` covers the
      no-database path with a mock.
- [x] **M** Playwright job in CI. Spec renamed to
      `e2e/pdf-upload.mocked.spec.ts`. The dev server is port 3100 so it does
      not reuse whatever is already on 3000. The in-flight spinner test holds
      the upload on a deferred promise instead of `setTimeout(400)`. Three
      assertions were updated to match the current page (native email
      constraint, a stable "Queued" mock, exact `50%`). No unmocked smoke test.

### A5. Docs — `docs/readme-and-cleanup`

Do after A2 so links point at final paths. Coordinate the OCR sections of the
README with Track B.

- [x] **S** Removed `docs/planning/INTERACTIVE_OCR_WORKFLOW.md` and its
      index entry. Links in the OCR plan and smoke doc point at the CLI guide
      and Track B.
- [x] **M** `README.md` is the pitch, features, architecture, quickstart,
      layout, and acknowledgments. No screenshot was in the repo, so none was
      added. OCR CLI, deployment, and troubleshooting moved to `docs/guides/`.
      `backend/BDRC/` is called out as vendored.
- [x] **S** Doc index points architecture and components at `frontend/docs/`.
      Archive links are gone. The broken README step numbering went away with
      the rewrite.
- [x] **S** Deleted `ARCHITECTURE_SIMPLE.md`, `docs/archive/`, and
      `docs/planning/BACKLOG.md`.
- [x] **M** `docs/adr/SPELLCHECKER_DECISIONS.md` is context, decision, and
      consequences per entry. Status emoji and the option lists are gone.
      The long form is in git history.
- [x] **S** Planning and research notes stay in the repo and are listed in
      `docs/README.md` as working notes, not as the public site. That includes
      `LIVE_PECHA_CAPTURE`, `PREPARE_FEATURE`, `WORD_CORPUS_PLAN`, and
      `EDUCATIONAL_CONTENT_PLAN`.
- [x] **S** `email.py` documents that send is log-only. `config.py` says
      Render, not Railway. Restating comments removed in
      `completeness_checks.py` and `parser.py`.
- [x] **S** Pull request template has a How tested section.
- [x] **M** `0.7.0` (2026-10-22) lists only what is live on the site: Learn,
      the redirects and nav, the spellcheck corpus sentence, and the
      `/interactive-ocr` waitlist. Local OCR assist, the diagnostician, vision,
      the corpus loader, and the lexicon migration are not in the public
      changelog.

### A6. Frontend shared code — `refactor/frontend-shared`

Shared frontend pieces for spellcheck and the rest of the app. The slimmed
OCR proofing page can adopt them when Track B happens; it does not have to
land first.

- [x] **S** `lib/config.ts`: single `getApiUrl()` (was duplicated in
      `lib/api.ts` and `lib/ocrAssist.ts`). Throws if
      `NEXT_PUBLIC_API_URL` is unset in production, on the first request
      rather than at import, so a production build without the variable
      still compiles.
- [x] **M** `lib/http.ts`: shared `request<T>()` + `parseError`. Spellcheck
      and OCR assist both use it. `APIError` lives here and is re-exported
      from `lib/api.ts`.
- [x] **S** `JobStatus` clears the poll timeout on unmount and reads
      `onCompleted` from a ref. A failed job already rendered its error;
      that path is unchanged.
- [x] **S** Empty spellcheck results render a text node. No
      `dangerouslySetInnerHTML`.
- [x] **M** `Alert`, `Spinner`, and `icons` are shared. Spellcheck text
      input already used `Button`; tabs already used `TabButton`. The amber
      PDF actions stay as they are, because `Button` only has the gray site
      variants. `PDFDownloadLink` takes `variant="pdf" | "docx"`.
- [x] **L** Learn tables and examples live in `content/learn/*.ts`.
      Shared chrome is `components/learn/` (`LearnHeader`, `ParticleTable`,
      `SyllableAnatomy`, `ErrorExample`, `WylieExample`). Page prose stays
      in the pages.

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

- [x] **S** Status note at the top of `docs/planning/INTERACTIVE_OCR_PLAN.md`
      points here. The rest of that plan stays as history.
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
