# OCR parity baseline

**Status:** Two golden fixtures locked (30 Oct 2026). Rotation flip fixed
(29 Oct 2026). Tashi Gyedpa demoted to routing-only. Fidelity coverage is now
**golden** fixtures — clean, in-distribution BDRC scans measured against
hand-typed transcriptions. Also landed in this pass: a native-image OCR path in
`extract_scanned` (fixes blank reads when a scan is wrapped in a larger page),
and Sanskrit reclassification in the spellcheck engine (mantras/dharanis become
info-level `foreign_transliteration` notes, not genuine errors).
**Branch:** `test/ocr-parity-baseline`
**Tests:** `backend/tests/test_ocr_parity.py`, `backend/tests/test_line_rotation.py`
**Fixtures:** `backend/tests/fixtures/parity/`

The point of these tests is a strong regression wall: prove that under the
right circumstances OCR reads a page near-perfectly, so any later change that
dents a known-good read fails review. That only works if the fixture input is
clean and in-distribution for the BDRC models (real pecha/book/woodblock
scans). A broken-font PDF that merely *routes* to OCR is not such an input.

Fidelity is pinned per fixture by a **golden baseline** (`_GOLDEN_OCR` in
`test_ocr_parity.py`): a tight genuine-error gap plus per-page Tibetan-character
floors. Never raise `max_gap` or lower a floor to make a change pass.

---

## What the test is for

For each pair in `backend/tests/fixtures/parity/`, spellcheck the plain-text file and spellcheck whatever `extract_pdf` returns for the PDF. The genuine-error counts should stay within the fixture's ceiling. Tsongkhapa Prayer is a normal digital PDF, uses the fitz path, and passes at tolerance 0. Leave it alone.

Tashi Gyedpa is a Word PDF set in Microsoft Himalaya. That font's ToUnicode CMap does not survive copy-out, so `extract_pdf` renders the pages and runs BDRC OCR. ADR-015 in `docs/adr/SPELLCHECKER_DECISIONS.md` is why. The cmap routing tests (`test_cmap_detection.py`, `test_pdf_extraction.py`) cover that decision.

**Why Tashi Gyedpa is not a fidelity fixture.** Its rendered page is pristine — crisp, correct uchen, no skew, no phantom glyphs (the phantom problem is in the text layer, which OCR never sees). OCR even reads its title line perfectly. But a few lines down it degrades, because Microsoft Himalaya is a modern digital Word font and the BDRC models are trained on actual pecha/woodblock/book scans — this rendering is out-of-distribution. It will never read perfectly, so it cannot be a "perfect read" wall. It stays only as the routing fixture (`_ROUTING_ONLY_FIXTURES`), and the parity oracle skips it.

---

## Rotation investigation (Tashi Gyedpa)

This section is the record of the rotation bug that the Tashi Gyedpa fixture
surfaced. It is history now that the fixture is routing-only, but it is why the
rotation fix exists and worth keeping.

Re-ran on 21 Oct 2026 against the ONNX files in `backend/Models` and `backend/OCRModels`, with OpenCV pinned at 4.9.0.80. No saved pytest log from the original day exists. CI has never run this fixture: models are not downloaded, and `_ocr_available()` skips it. Locally it is also `@pytest.mark.slow`, so `pytest -m "not slow"` skips it too.

| Commit | Date | Copy-paste errors | OCR errors | Gap | Page 1 |
| --- | --- | --- | --- | --- | --- |
| `46a9e71` (#43), fixture added | 15 Apr 2026 | 7 | 26 | 19 | title intact, 623 Tibetan characters |
| `7704e60`, last commit before the OCR sync | 11 Jun 2026 | 5 | 24 | 19 | same read as April (2161 Tibetan characters across 4 pages) |
| `117720c` (#67), upstream OCR sync | 27 Aug 2026 | 5 | 37 | 32 | rotated to 179.78°, 77 characters |
| `fix/deps-and-upload-hardening` | 21 Oct 2026 | 5 | 35 | 30 | still flipped, 77 characters |

The April and June OCR text match. The spellchecker's own error count on the plain text moved from 7 to 5 in that window; the gap stayed 19. The test was already over its tolerance on the day it was added.

`117720c` is the change that made it worse. `backend/BDRC/UPSTREAM.md` calls the rotation edit a sign fix: `-(90 - mean)` became `90 + mean`, with `max_angle` lowered from 5° to 2°. On this OpenCV, page 1's line rectangles come back near +90°, and the new formula turns that into 179.78°. Page 1 collapses. Page 2's Tibetan character count also moved (494 → 682) and page 4's moved (509 → 479), so the sync was more than the one rotation line. The page-by-page render on the current branch did not create the gap.

**Rotation fix (29 Oct 2026).** `get_rotation_angle_from_lines` and
`calculate_rotation_angle_from_lines` now share `_mean_line_skew`, which folds
each `minAreaRect` angle into a tilt inside `(-max_angle, max_angle)` and
returns 0 otherwise. A near-90° rectangle becomes a small ±tilt instead of a
~180° flip. `backend/tests/test_line_rotation.py` locks the clockwise case that
used to return ~180°. After the fix, Tashi Gyedpa page 1 reads **640** chars
again (was 77); pages are `(640, 682, 539, 479)`. The genuine-error gap rose
30 → 43 because a recovered page 1 now has a full page of misreads to flag,
where the collapsed page flagged almost none. The per-page floor — not the gap —
is the guard against the collapse returning.

Per-page Tibetan characters across the saga:

| Page | Before `117720c` | After `117720c` / today |
| --- | --- | --- |
| 1 | 623, starts `འཕགས་པ་བཀྲ་ཤིས་བརྒྱད་པ` | 77, starts `ཨུ་` |
| 2 | 494 | 682 |
| 3 | 535 | 536 |
| 4 | 509 | 479 |
| Total | 2161 | 1774 |

Plain text is 2091 Tibetan characters and 5 genuine errors (today's engine).

---

## Decisions

| Decision | Choice |
| --- | --- |
| Where | Its own branch, `test/ocr-parity-baseline`. Not mixed into upload hardening or the vision/diagnostician cut. |
| What a golden baseline means | A tight gap + per-page floors measured once on a clean, in-distribution scan against a trusted transcription. The wall fails if the gap grows or a page collapses. Ideal gap is 0; a larger measured value states the engine's real ceiling on that page. |
| Tashi Gyedpa | Routing-only (`_ROUTING_ONLY_FIXTURES`). Rendered glyphs are out-of-distribution modern uchen; it will never read perfectly, so it is not a fidelity fixture. Cmap routing tests keep its `.pdf`. |
| Golden fixture source | A clean scan of real Tibetan text that is in-distribution for BDRC (pecha / woodblock / book), not a phone photo and not a modern Word-font render. Phone capture noise belongs to `LIVE_PECHA_CAPTURE.md`. |
| Ground truth | Typed from, or verified against, a trusted digital edition — never transcribed from the OCR output, which would make the test circular. |
| Rotation formula | Fixed 29 Oct 2026 via `_mean_line_skew`'s fold into ±`max_angle` (see "Rotation fix"). |
| Scan rendering | `extract_scanned` OCRs the embedded full-page image at native resolution for single-image pages (honouring `/Rotate`), falling back to a 300-DPI page render otherwise. Fixes scans wrapped in a larger page reading blank. |
| Sanskrit in the engine | `check_text` reclassifies errors on likely-Sanskrit syllables to info-level `foreign_transliteration` (critical encoding errors excepted). Detection is centralized in `sanskrit.py` and shared with `quality.py`. |
| Common Sanskrit allowlist | `COMMON_SANSKRIT` in `rules/exceptions.py` makes the ubiquitous forms (oṃ, āḥ, hūṃ, vajra, padma, svāhā, phaṭ) silently valid. Curated + conservative; complements the heuristic, which covers the long tail. |
| What "genuine error" counts | `severity != "info"`. Sanskrit notes and non-Tibetan-skipped notes are excluded from the gap on both sides. |
| CI models | The suite keeps skipping in CI when `Models/Lines/PhotiLines.onnx` is absent. Running it is a local step before any OCR or extractor change. Caching models in CI is a later decision. |

---

## Order of work

### 1. Fix the rotation flip — DONE (29 Oct 2026)

`get_rotation_angle_from_lines` no longer flips upright pages (see "Rotation
fix"). `backend/tests/test_line_rotation.py` locks the clockwise case. This was
a real bug independent of fixture choice.

### 2. Demote Tashi Gyedpa to routing-only — DONE (30 Oct 2026)

- `_ROUTING_ONLY_FIXTURES = {"Tashi Gyedpa"}`; the parity oracle skips it.
- Its `.pdf` stays in `parity/` for `test_cmap_detection.py`.
- The old ratchet entry is removed. The fidelity machinery is reframed as
  `_GOLDEN_OCR` / `GoldenOCRBaseline`.
- Tsongkhapa stays at tolerance 0 (digital, fitz path).

### 3. Golden fixtures from BDRC scan W28732 — DONE (30 Oct 2026)

Two single-page fixtures from W28732 v15, both in-distribution pecha scans:

| Stem | Page | Role | max_gap | Floor | allowed_extra |
| --- | --- | --- | --- | --- | --- |
| `tibetan-baseline-W28732` | 8 | Predominantly Tibetan body text | 0 | 820 | `double_vowel` |
| `menla-sadhana-sanskrit-W28732` | 1 | Sanskrit-heavy (mantras/seed syllables) | 2 | 753 | `consonant_after_vowel`, `unparsed_characters` |

Notes from locking them:
- **The body page reads at gap 0** — the "right circumstances" claim holds. Its
  one artefact is the hung seed syllable ཧཱུྂ: OCR sometimes drops the
  candrabindu, yielding ཧཱུ, which is no longer a Sanskrit marker and so shows
  as a `double_vowel` rather than an info note (hence the recorded extra).
- **Menla is the harder Sanskrit page** (gap 2): a few genuine OCR misreads
  including an injected Latin glyph, a stray `+` prefix, and a
  consonant-after-vowel.
- **Common Sanskrit is allowlisted.** The ubiquitous, unambiguous forms (ཨོཾ,
  ཨཱཿ, ཧཱུྂ, བཛྲ, པདྨ, སྭཱཧཱ, ཕཊ) are in `COMMON_SANSKRIT` in
  `rules/exceptions.py` → silently valid, no flag. This fixes the heuristic's
  false negatives (e.g. isolated བཛྲ) and dropped menla's gap from 3 to 2. The
  heuristic detector still handles the long tail as info notes. Allowlisting
  padma also removed `unparsed_characters` from menla's copy side, so the
  OCR-only garbage reads now surface as a recorded `allowed_extra` type.
- **"Genuine error" is now severity-based.** `_genuine_error_count` counts
  `severity != "info"`, so the engine's Sanskrit `foreign_transliteration`
  notes do not inflate the gap. `INFO_ONLY_TYPES` excludes those info
  categories from the error-type comparison too.
- **Native-image OCR.** Both source PDFs wrap a 4352×1088 pecha strip inside a
  US-Letter page; rendering the page at 300 DPI shrank the strip to a band and
  OCR read nothing (0 chars). `extract_scanned` now OCRs the embedded full-page
  image at native resolution for single-image pages, honouring `/Rotate`, and
  falls back to page rendering otherwise. Guarded by `test_extract_scanned.py`.

Rejected candidate: **page 1 (title page).** Clean to a human eye but OCRs as
incoherent soup even after cropping the frame/side-panels and 2× upscaling. Its
ornamental title calligraphy is out-of-distribution for the body-text-trained
recognizer. Not a golden fixture; dropped (not added to `parity/`).

Earlier capture attempts (29 Oct 2026), for the record:
- **Screenshots** of practice pages: too small; OCR collapsed or garbled them.
- **Phone photos** (`IMG_4572/4573`): large enough and now upright after the
  rotation fix, but still OCR with heavy noise. Not clean enough to be golden.
  Hold until recognition is clean, not just upright.

### 4. Point the skill at the golden design — DONE

`.cursor/skills/spellcheck-ocr-parity/SKILL.md` describes the per-fixture golden
baseline, the per-page floors, the slow-marker/models caveat, and the local
pytest command. The "raise the tolerance" guidance is removed.

---

## Out of scope

- Raising `max_gap` or lowering a page floor to make a failing read pass.
- Making Tashi Gyedpa (or any out-of-distribution font render) a fidelity fixture.
- Downloading ONNX models in GitHub Actions.
- Phone-photo fixtures until recognition is clean. See `LIVE_PECHA_CAPTURE.md`.
- Vision or the diagnostician as a way to pass the test.
