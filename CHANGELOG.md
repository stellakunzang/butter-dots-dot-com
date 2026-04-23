# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Changed

- Lexicon data is stored relationally: `word`, `source`, `word_source`, and `definition` replace JSONB on the old spelling list; `lexicon_staging_line` is there for upcoming ingest. Existing databases can run `database/migrations/002_lexicon_schema.sql`; fresh installs use the updated `schema.sql`. `DictionaryService`, `build_corpus.py`, and `seed_corpus.py` target the new tables.

---

## [0.6.1] - 2026-04-16

### Fixed

- Tibetan syllable parser falsely flagged **འོ** (achung + o-vowel) on valid forms such as **བྱའོ**, **པོའོ**, and **མཐོའོ**. The **འི** path is now generalized: shared `ACHUNG_SUFFIX_VOWELS` (ི, ོ), one detect/parse pipeline, and completeness rules aligned so two vowel marks are allowed when the second sits on suffix **འ**.
- Spelling rules page: **རུ་** locative example updated from **རྒྱལ་ཁབ་རུ་** to **བཀའ་རུ་**. A **བ** suffix takes **ཏུ་** (e.g. **རྒྱལ་ཁབ་ཏུ་** “to/in the kingdom”), not **རུ་**, which only follows **འ** or no suffix—consistent with the particle rules in the spellchecker.

---

## [0.6.0] - 2026-04-15

### Fixed

- Docker Compose startup failure caused by `confidence_score` index referencing a non-existent column in `schema.sql` and `001_add_spelling_reference.sql`

### Added

- `TabButton`, `PDFDownloadLink`, and `ResetLink` extracted as shared components
- `Button` component gains `disabled` and `type` props

### Changed

- `TextInput` Clear and Submit buttons now use the shared `Button` component
- `spellcheck.tsx` `useEffect`-to-reset-state anti-pattern replaced with `checkedText`/`isStale` derived flag
- `PDFUpload` internal `selectedFile` state removed; parent-owned state passed as prop
- `ResultLink` (spellcheck.tsx) and `DownloadButton` (JobStatus.tsx) consolidated into shared `PDFDownloadLink`

---

## [0.5.0] - 2026-04-15

### Added

- Upload size cap (50 MB) on PDF endpoints; returns HTTP 413 on oversized files
- `max_length=100_000` on text spellcheck input to prevent event-loop blocking
- Async page limit restored: PDFs ≤ 15 pages sync, larger PDFs routed to background queue

### Changed

- `TibetanSpellChecker` and `DictionaryService` now shared as module-level singletons — DB corpus loaded once at startup instead of per request
- CPU-bound PDF processing steps (`extract_pdf`, `annotate_pdf`, `build_docx`, `check_text`) offloaded to thread pool via `asyncio.to_thread` to keep the event loop unblocked

### Removed

- Unused `checkHealth` function and `PDFResultURLs`, `SpellCheckRequest` interfaces from frontend API client
- Unused `EmailStr` import from spellcheck schemas; `email-validator` dependency dropped
- Unused `pyctcdecode` and `thin-plate-spline` dependencies
- Stale archive docs: `REFACTORING_SUMMARY.md`, `MIGRATION_COMPLETE.md`, `SETUP_COMPLETE.md`, `RTF_QUICK_START.md`
- Stale conversational artifact from `WORD_CORPUS_PLAN.md`

---

## [0.4.0] - 2026-04-14

### Added

- Dictionary-based word lookup (Phase 2) — structurally valid syllables are now
  checked against a corpus of attested Tibetan words and flagged as `unknown_word`
  if absent, surfaced as yellow warnings distinct from red structural errors
- `spelling_reference` database table with normalized lookup, source tracking,
  dialect and Sanskrit flags, and four indexes for fast access
- `DictionaryService` — loads corpus at startup, extracts every valid syllable
  from multi-syllable entries, O(1) frozenset lookup; degrades silently when no
  database is configured
- Corpus build scripts: `build_corpus.py` with scaffolded extractors for THDL,
  Rangjung Yeshe, and Monlam; `seed_corpus.py` with ~55 hand-verified words for
  pipeline testing
- `corpus_hit` field on Phase 1 structural errors — flags when a flagged syllable
  is nonetheless attested in the corpus, useful for monitoring potential false
  positives over time
- Structured JSON logging on every spell check (`spellcheck_result` tag) with
  aggregate counts for analysis via `grep | jq`
- `GET /api/v1/corpus/stats` endpoint

---

## [0.3.0] - 2026-04-01

### Added

- PDF spellcheck pipeline — upload a Tibetan PDF, get back an annotated DOCX with
  each structurally invalid syllable marked; supports both digital PDFs and
  scanned documents via OCR fallback
- Async job support for PDF processing — upload returns a job ID; frontend polls
  until complete
- BDRC ONNX OCR engine for scanned PDFs, replacing Tesseract; model files
  excluded from version control
- Broken-CMap detection for digital PDFs — automatically falls back to OCR when
  the PDF's character map is corrupt or missing (ADR-015)
- OCR/copy-paste parity tests — fixture-based regression tests verifying that the
  OCR and digital extraction paths produce equivalent spellcheck results
- PDF spell check UI — upload form, job progress polling, email capture, results
  display
- Shared `PageTitle` and `SectionHeading` typography components adopted across
  static pages

### Changed

- Particle validation tightened: ས, ར, ཞིག, and ཅིག marked as lenient to reduce
  false positives; ཏུ handling improved; locative suggestions refined
- PDF annotation and DOCX export refactored to syllable granularity
- Digital PDF extraction migrated from pdfplumber to fitz for better CMap support

### Removed

- JSON download endpoint removed from PDF spellcheck pipeline

---

## [0.2.0] - 2026-03-12

### Added

- Particle spelling rules — context-aware validation of relational, agentive,
  locative, and indefinite article particles against the suffix of the preceding
  word, with suggestions for the correct form
- Excepted words — ནའང་ and ལའང་ are now recognized as grammatically valid by
  convention and no longer flagged
- Tibetan numeral syllables (U+0F20–U+0F33) are now silently skipped; numbers no
  longer produce false positives or break particle context
- Tibetan punctuation and mark characters (yig mgo openers ༄ ༅, decorative shad
  variants ༑ ༒, gter tsheg ༔, etc.) are now silently skipped
- Spelling Rules page — learner-facing reference documenting syllable anatomy,
  particle rules by category, and an explanation of each error type
- Changelog page — release notes published on the frontend at /changelog

### Fixed

- ཧཧིབ་ was not being flagged as invalid; ཧ (ha) cannot act as a prefix and is
  now correctly detected as an unparsed character
- "Relational" used throughout in place of "genitive" for the bdag gi sgra
  particle category, matching standard English terminology for this community

### Changed

- Subscript validation re-enabled after confirming the rule data is correct and
  no false positives occur on attested Tibetan words

---

## [0.1.0] - 2026-02-09

### Added

- Tibetan syllable spellchecker — validates the structural correctness of
  Tibetan syllables against classical spelling rules
- Validates all five prefix consonants (ག་ ད་ བ་ མ་ ར་) against valid root
  consonant combinations
- Validates superscripts (ར་ ལ་ ས་), subscripts (ྱ ྲ ླ ྭ), suffixes, and
  post-suffixes
- Detects impossible syllable structures: subscripts appearing after vowels or
  suffixes, multiple vowel groups, unusual mark positions
- Detects syllables that exceed the maximum valid length
- Web interface for checking Tibetan text inline
- Wylie transliteration shown alongside each flagged syllable for reference
