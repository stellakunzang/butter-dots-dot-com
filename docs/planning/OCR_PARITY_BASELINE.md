# OCR parity baseline

**Status:** Not started. Not ticketed. Separate from Track A and from the OCR-assist cut.
**Branch:** `test/ocr-parity-baseline`
**Tests:** `backend/tests/test_ocr_parity.py`
**Fixtures:** `backend/tests/fixtures/parity/`

The Tashi Gyedpa parity tests were sidelined, then OCR code changed, and there was no green baseline to show that the read had gotten worse. This plan records the measurements and the order of work so the next OCR change has a number to beat.

Do not do this on `fix/deps-and-upload-hardening` or on the OCR-assist cut branch. Do not raise `_PER_FIXTURE_TOLERANCE` on those branches either.

---

## What the test is for

For each pair in `backend/tests/fixtures/parity/`, spellcheck the plain-text file and spellcheck whatever `extract_pdf` returns for the PDF. The genuine-error counts should stay within the fixture's tolerance. Tsongkhapa Prayer is a normal digital PDF, uses the fitz path, and passes at tolerance 0. Leave it alone.

Tashi Gyedpa is a Word PDF set in Microsoft Himalaya. That font's ToUnicode CMap does not survive copy-out, so `extract_pdf` renders the pages and runs BDRC OCR. ADR-015 in `docs/adr/SPELLCHECKER_DECISIONS.md` is why. The cmap routing tests (`test_cmap_detection.py`, `test_pdf_extraction.py`) already cover that decision. The parity test is the fidelity check: does the OCR text spellcheck like the known prayer?

Those two jobs got bundled into one fixture. The font problem is a reason the fidelity failure was easy to discount. An image of the same text is the fidelity fixture. The Himalaya PDF stays as the routing fixture.

---

## Measured baseline

Re-ran on 21 Oct 2026 against the ONNX files in `backend/Models` and `backend/OCRModels`, with OpenCV pinned at 4.9.0.80. No saved pytest log from the original day exists. CI has never run this fixture: models are not downloaded, and `_ocr_available()` skips it. Locally it is also `@pytest.mark.slow`, so `pytest -m "not slow"` skips it too.

Tolerance has been 10 since the fixture was added. The comment in `test_ocr_parity.py` says the prayer "can differ by ~5 syllables." A re-run of that commit does not produce a gap of 5.

| Commit | Date | Copy-paste errors | OCR errors | Gap | Page 1 |
| --- | --- | --- | --- | --- | --- |
| `46a9e71` (#43), fixture added | 15 Apr 2026 | 7 | 26 | 19 | title intact, 623 Tibetan characters |
| `7704e60`, last commit before the OCR sync | 11 Jun 2026 | 5 | 24 | 19 | same read as April (2161 Tibetan characters across 4 pages) |
| `117720c` (#67), upstream OCR sync | 27 Aug 2026 | 5 | 37 | 32 | rotated to 179.78°, 77 characters |
| `fix/deps-and-upload-hardening` | 21 Oct 2026 | 5 | 35 | 30 | still flipped, 77 characters |

The April and June OCR text match. The spellchecker's own error count on the plain text moved from 7 to 5 in that window; the gap stayed 19. The test was already over its tolerance on the day it was added.

`117720c` is the change that made it worse. `backend/BDRC/UPSTREAM.md` calls the rotation edit a sign fix: `-(90 - mean)` became `90 + mean`, with `max_angle` lowered from 5° to 2°. On this OpenCV, page 1's line rectangles come back near +90°, and the new formula turns that into 179.78°. Page 1 collapses. Page 2's Tibetan character count also moved (494 → 682) and page 4's moved (509 → 479), so the sync was more than the one rotation line. The page-by-page render on the current branch did not create the gap.

Per-page Tibetan characters after the sync (the ratchet to lock):

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
| Where | Its own branch, `test/ocr-parity-baseline`, after the current core branch lands. Not mixed into upload hardening or the vision/diagnostician cut. |
| What "baseline" means | A ratchet at today's measured read. The test fails when the gap grows or a page's Tibetan character count drops. It does not fail merely because the gap is larger than 10. |
| What the tolerance of 10 means | An aspiration from the day the fixture was added. It is not the baseline. Do not raise it to 30 and call the test fixed. |
| Himalaya PDF | Stays in the tree. Cmap routing tests keep using it. It stops being the only fidelity oracle. |
| Image fixture | Same `Tashi Gyedpa.txt`, new image-only PDF. First run records that fixture's own ratchet. Do not copy the Himalaya numbers onto it. |
| Image source | A rendered page image of the known text, not a phone photo. A photo mixes in camera noise; that question belongs to `LIVE_PECHA_CAPTURE.md`. |
| Rotation formula | Investigated after the ratchet is in place, on a follow-up commit. The first commit only locks today's numbers, so the repair has something to move. |
| CI models | Not in the first step. The suite keeps skipping in CI when `Models/Lines/PhotiLines.onnx` is absent. Running it is a local step before any OCR or extractor change. Caching models in CI is a later decision. |

---

## Order of work

### 1. Lock today's Himalaya read

On the new branch, change the Tashi Gyedpa assertion so a worse read fails and today's read passes.

- Record the genuine-error gap (30 as of 21 Oct 2026) and the four page character counts in the test, next to the fixture, with the date and the commits above.
- Fail if the gap increases, or if any page's Tibetan character count drops past the recorded count by more than a few characters.
- A single gap ceiling is not enough. Page 1 can collapse while another page gets longer and the gap barely moves. The per-page counts are what caught the August sync.
- Delete the instruction that says to update `_PER_FIXTURE_TOLERANCE` when an OCR fixture fails. That sentence is how a real miss gets silenced.
- Keep Tsongkhapa at tolerance 0.

Run, with models present:

```bash
cd backend && venv/bin/pytest tests/test_ocr_parity.py -v
```

That command has to be part of review for any later change under `backend/BDRC/`, `backend/app/pdf/extractor.py`, or `backend/app/pdf/ocr.py`. `pytest -m "not slow"` will not run it.

### 2. Add the image fixture

Render `Tashi Gyedpa.txt` to an image-only PDF (no text layer, so `extract_pdf` must take the OCR path). Put it beside the text under a new stem so the Himalaya pair is unchanged.

Run the parity test once and write down that run's gap and per-page character counts. That is this fixture's ratchet. Then the same assertion as step 1 applies.

The Himalaya pair remains the "this font still routes to OCR, and that route has not gotten worse" check. The image pair is "BDRC on a clean page of this prayer." Routing coverage stays in the cmap tests either way.

### 3. Only then touch the OCR read

With both ratchets green, a follow-up commit can repair the rotation formula from `117720c`. Expect page 1's character count to move back toward ~623 and the Himalaya gap to move from ~30 toward the pre-sync 19. Update the ratchet to the new, better numbers in that same commit, so the ceiling cannot drift back up.

19 is still over the original tolerance of 10. Closing that remaining gap is further work (line segmentation, the `ཨ` repetition on later pages). It is not required to call the baseline done.

### 4. Point the skill at the ratchet

`.cursor/skills/spellcheck-ocr-parity/SKILL.md` still says the default tolerance is 2 and that a noisy scan should raise `OCR_ERROR_COUNT_TOLERANCE`. Update it to the per-fixture ratchet, the image-fixture steps, and the local pytest command above.

---

## Out of scope

- Raising the tolerance until the assertion is green.
- Deleting Tashi Gyedpa because the font is awkward.
- Fixing `get_rotation_angle_from_lines` in the baseline commit.
- Downloading ONNX models in GitHub Actions.
- Phone-photo fixtures. See `LIVE_PECHA_CAPTURE.md`.
- Vision or the diagnostician as a way to pass the test.
