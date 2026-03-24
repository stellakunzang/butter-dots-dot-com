# Feature Backlog

Unscheduled ideas and future feature candidates. Items here have been identified
as worth building but have not yet been prioritized or planned. Items that were
explicitly deferred during development are noted with their source ADR.

---

## Active deferrals — disabled infrastructure

These features were built but then disabled or bypassed. The code exists; the
decision to ship them is pending.

### Async processing with email delivery for large PDFs

**Summary**: PDFs above a page threshold get queued in the background; results
are emailed when ready rather than making the user wait.

**Background**: The full async pipeline — `_queue_async_job`,
`_background_process`, progress tracking, and `send_results_email` — is
implemented in `backend/app/api/spellcheck.py`. It was wired to a 15-page
threshold and then disabled (see the `TODO` comment around line 155) because we
hadn't gathered enough user feedback to know whether async delivery was wanted.

**What's needed to re-enable**:

- Decide on the page threshold (15 pages feels reasonable as a starting point)
- Configure an email provider: the `send_results_email` stub in
  `backend/app/utils/email.py` needs a real transport (Resend, SendGrid, AWS
  SES, or SMTP)
- Update the upload endpoint to route large PDFs through `_queue_async_job`
- Update the frontend to handle `PDFUploadAsyncResponse` — show a "we'll email
  you" confirmation instead of a spinner

**Open questions**:

- Do we want to require an email address for large PDFs, or only prompt for it?
- Should small PDFs also offer the email option for users who prefer async?

---

## Spell checker — next phases

### Phase 2: Word-level spell checking

**Summary**: Check whether syllables form real Tibetan words, not just whether
they are structurally valid.

**Background**: Phase 1 (shipped) validates syllable grammar. Phase 2 adds a
dictionary lookup layer. A structurally valid syllable like `ཡིབ` would be
flagged because it does not appear in the word corpus. Contextual suggestions
("did you mean `ཡིག`?") become possible once we have frequency data. (ADR Phase
Breakdown, Phase 2 section)

**Depends on**: Word corpus (see below)

**What's needed**:

- Build and load the word corpus (see separate item)
- Dictionary lookup in the spell check engine
- Suggestion generation with frequency-based ranking
- Updated frontend error display: distinguish "structurally invalid" vs "valid
  syllable, unknown word"

### Word corpus — sourcing and build

**Summary**: Populate the `spelling_reference` table with 30,000–50,000
validated Tibetan words from multiple sources.

**Background**: The database schema is designed for this (ADR-008, ADR-013). The
plan is to cross-reference THDL, Rangjung Yeshe Wiki, and Monlam, keeping only
words that appear in 2+ sources. The build scripts in
`docs/planning/WORD_CORPUS_PLAN.md` are the starting point.

**What's needed**:

- Confirm licensing for THDL and Rangjung Yeshe (likely open; Monlam needs
  contact)
- Write extraction and cross-reference scripts
- Quality spot-check and load to database
- Measure coverage on real sample texts from the sangha

### "Did you mean" — correction suggestions

**Summary**: When a syllable or word is flagged, suggest the most likely
intended word.

**Background**: Mentioned in ADR-014 Future Improvements. Requires Phase 2 word
corpus to be useful. Could use edit-distance (Levenshtein) against the corpus,
weighted by syllable frequency.

**Depends on**: Phase 2 word corpus

### Sanskrit handling

**Summary**: Avoid false positives on Sanskrit mantras and technical Buddhist
terms (e.g., `ཨོཾ་མ་ཎི་པདྨེ་ཧཱུྃ`, `དྷརྨ`).

**Background**: Sanskrit words in Tibetan use special stacking rules (ha
subscript for aspirated consonants, retroflex consonants) that are illegal under
normal Tibetan grammar. Currently these are flagged as errors. The approach is a
Sanskrit whitelist for Phase 2, with fuller rule-based Sanskrit validation in
Phase 3. (ADR-011)

**Options**:

1. Maintain a curated whitelist of common Sanskrit terms (mantras, technical
   Buddhist vocabulary) — bypass spell check for these
2. Detect the Sanskrit-specific Unicode letters (`དྷ`, `གྷ`, `བྷ`, `ཊ`, `ཋ`,
   `ཌ`, `ཌྷ`, `ཎ`) and mark the syllable as "Sanskrit" rather than "error"
3. Phase 3: proper Sanskrit grammar rules

### Parser improvement — complex syllable misparsing

**Summary**: `བརྒྱུད` and similar complex stacked syllables are noted as
misparsed in the current implementation.

**Background**: Flagged in ADR-014 Future Improvements. Likely rare in practice
(the syllable-structure completeness layer catches most cases) but worth
resolving before Phase 2 to avoid false positives on valid complex words.

---

## Transliteration generator

**Summary**: Given Tibetan Unicode text, produce a readable romanized phonetic
rendering using THL Simplified Phonetics.

**Motivation**: Practitioners who cannot yet read the script benefit from
phonetic renderings of prayers and liturgical texts. Pairs naturally with the
spellchecker and OCR pipeline — OCR a PDF, spellcheck it, get a phonetic version
for practice use.

**Scope decision**: THL Simplified Phonetics is the target system. It is
practitioner-friendly and used by many Tibetan Buddhist centers. (Wylie is
already shown inline in the spellchecker error display; a standalone
transliteration page would serve a different use case.)

**Open questions**:

- Does a Python library exist for THL phonetics, or do we need to implement the
  rules? (Wylie conversion is trivial via `pyewts`; THL phonetics is more
  involved — it requires pronunciation rules and is dialect-sensitive)
- Which dialect as default? U-Tsang is the best-documented; Amdo would be more
  relevant to this community but the phonetic rules are less formalized
- Input surface: raw textarea only, or also accept uploaded PDFs/text files?
- Output options: plain block of romanized text, or interlinear (Tibetan above,
  phonetics below)?

**Notes from ADR-009**: The ADR planned for multiple transliteration systems
(THL Simplified, eventually Amdo phonetics) with user-selectable preference. The
standalone transliteration page could also serve as the entry point for that
broader feature.

---

## Community and quality

### User-submitted words (community corpus)

**Summary**: Allow users to flag a word as incorrectly marked, submit it to the
spelling reference, and have it reviewed and approved.

**Background**: The spelling reference will always have gaps. ADR-012 designed
this in detail including the database schema (`word_submissions` table), the
user flow, quality control (auto-approve after 3 independent submissions), and a
moderation interface.

**Depends on**: Phase 2 word corpus (need a corpus to have gaps worth reporting)

**What's needed**:

- User accounts or at minimum a session/email-based submission flow
- `word_submissions` table in the database schema
- Moderation interface (admin-only page)
- Frontend: "This word is correct — submit it" action on error items

### Amdo dialect support

**Summary**: Mark certain words as Amdo-dialect variants and treat them as valid
even if they diverge from standard U-Tsang orthography.

**Background**: This community uses the Amdo dialect. ADR-009 flags this as
critical. The `dialect` column in the `spelling_reference` schema was designed
with this in mind. In practice this means: gathering Amdo-specific word lists
and, longer-term, Amdo phonetic rules for the transliteration feature.

---

## Educational content (`/learn` section)

**Summary**: A set of learner-facing pages explaining Tibetan script, Unicode
encoding, syllable structure, and the Wylie vs pronunciation distinction.

**Background**: `docs/research/EDUCATIONAL_CONTENT_PLAN.md` specifies five pages
in detail:

| Page                   | URL                         | Content                                     |
| ---------------------- | --------------------------- | ------------------------------------------- |
| Tibetan Script         | `/learn/tibetan-script`     | Syllable anatomy with interactive breakdown |
| Unicode Explained      | `/learn/unicode-explained`  | Code points, normalization, developer guide |
| Syllables vs Words     | `/learn/syllables-vs-words` | Why Phase 1 can't catch all errors          |
| Wylie vs Pronunciation | `/learn/wylie-problem`      | The written/spoken divide                   |
| How It Works           | `/learn/how-it-works`       | The full OCR → check → annotate pipeline    |

None of these have been built yet. The spellchecker UI currently links to
`/spelling-rules` for rule reference, but there is no general educational
section.

---

## Infrastructure

### Celery + Redis job queue

**Summary**: Replace FastAPI `BackgroundTasks` with a proper job queue for
processing large PDFs.

**Background**: ADR-004 chose BackgroundTasks for the MVP with an explicit note
to design for Celery migration. BackgroundTasks does not survive server
restarts, has no retry logic, and cannot scale horizontally. This matters once
the async PDF flow is re-enabled and if load increases.

**When to prioritize**: After the async email flow is re-enabled and if we start
seeing dropped or lost jobs.

### Real-time progress updates (SSE)

**Summary**: Replace the polling-based job status endpoint with Server-Sent
Events so the frontend gets push updates as a large PDF is processed.

**Background**: Noted as an alternative in ADR-002. The progress field is
already tracked in the job store (0–100). SSE would eliminate polling and give
the user a genuine live progress bar.

**Depends on**: Async email flow re-enabled (only useful once there are
long-running jobs the user might watch)

---

## "Prepare" — document conversion & style guide

**Summary**: Upload a PDF, DOCX, or RTF and receive a properly styled,
editable DOCX that applies the community's typography conventions (named
paragraph styles for Tibetan Body, English Transliteration, Tibetan Title,
etc.) ready to open in Pages, Word, or Google Docs.

**Motivation**: Community members regularly need to update sadhana texts but
only have PDFs or poorly-formatted source files. The current workflow is fully
manual. This feature automates the conversion step while preserving fonts,
sizes, and colors.

**Full plan**: `docs/planning/PREPARE_FEATURE.md`

**Needs before starting**:
- The final Pages-exported reference PDF (source of truth for style calibration)
- Decision on whether RTF input is in scope for v1 (adds LibreOffice to Docker)

---

## Phase 3 — advanced features (longer horizon)

Items that were explicitly scoped out of the current development arc and require
significant research or infrastructure before they are worth planning:

- **Grammar checking**: Not just spelling — detect grammatically incorrect
  particle usage, verb forms, etc. (Phase 3 in the ADR)
- **Historical spelling variants**: Some classical texts use archaic spellings
  that differ from modern convention; these should not be flagged as errors
- **Amdo phonetic transliteration rules**: The Amdo dialect has distinct
  pronunciation patterns relative to U-Tsang. Documented Amdo phonetic rules
  would be needed before this is feasible
