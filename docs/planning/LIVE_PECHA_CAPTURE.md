# Live Pecha Capture (Continuity Camera → OCR)

**Status:** Spike paused after two sittings — [#79](https://github.com/stellakunzang/butter-dots-dot-com/issues/79) stays open. The sitting harness and the line-splitting fixes it found merged to `main` in 0.9.0 (2026-11-18). Not ticketed for a product capture UI.  
**Companion to:** [INTERACTIVE_OCR_PLAN.md](INTERACTIVE_OCR_PLAN.md)  
**Continue here:** [Pick up here (next branch)](#pick-up-here-next-branch).  
**Goal:** Document a frictionless page-by-page capture loop for physical pecha, learn Continuity Camera + per-page OCR latency via a spike, then decide whether to ticket a product UI.

---

## Usecase

You have a physical pecha (often 200+ pages) that needs to become a workable digital file (DOCX / spellchecked text). Today the efficient-looking path is inefficient in practice:

1. Photograph each page on iPhone  
2. Save to Photos / sync via iCloud  
3. Open on Mac  
4. Upload one-by-one (or assemble a PDF offline)

That handoff dominates the session. You already use the iPhone as a Zoom webcam from the Mac — that feature is **Continuity Camera**. The proposed product path is: open the app on the Mac, select the iPhone camera in-browser, capture stills from the live stream, run OCR, and never touch the Photos library.

**Success shape for a book:**

- Most pages: BDRC accepts on the first good frame (local ONNX, no LLM cost).  
- Small percentage: text is special (warped, faded, mixed script, unusual layout) → flag for human proofing in `/ocr-assist`.  
- Bad frames: retake **the same page** immediately before advancing.

This is the “physical-book photos” future item from the interactive OCR plan, made concrete for Apple Continuity Camera + a live OCR gate.

---

## Decisions (v1)

| Decision | Choice |
| -------- | ------ |
| Device handoff | Continuity Camera → Mac browser `getUserMedia` (not Photos / iCloud / manual upload). **Safari only for now** — Chrome does not list the iPhone |
| Line fit | Three fixes in the vendored pipeline (they also run in production): frame-rule whitening above line 1, a first-line top bound of one median line gap, and a white margin when a line's ink would fill >95% of the 100-row window. Guarded by the `pecha-photo-*` golden fixtures. See [Spike notes, 2026-11-04](#spike-notes-2026-11-04) |
| Advance gate | **Live OCR gate** — wait for BDRC + quality score on the current page before flipping to the next |
| Pipelining | **Not in v1** — no “frame next while OCR last” (easy to confuse when holding a pecha) |
| Still source | Freeze frame / shutter from the video stream, not a file from the Photos library |
| Escalation | Human proofing in the slimmed `/ocr-assist` (edit, rotate, retry with a chosen BDRC model). No vision or diagnostician — removed in [CODE_REVIEW_FIXES.md](CODE_REVIEW_FIXES.md) B1 |
| Autocapture | Optional after spike proves framing + stability heuristics; not required for first spike |

---

## Proposed v1 loop (live OCR gate)

```mermaid
flowchart TD
  frame[Frame pecha on Continuity Camera]
  capture[Manual or auto capture still]
  imageQA[Optional fast image QA blur framing]
  ocr[BDRC OCR plus quality score]
  decide{Accept score?}
  retake[Discard still retake same page]
  accept[Commit page advance]
  escalate[Flag for human proofing]

  frame --> capture --> imageQA --> ocr --> decide
  decide -->|no image or OCR bad| retake --> frame
  decide -->|yes| accept
  decide -->|pathological| escalate
```

### Loop details

1. **Frame** — iPhone aimed at the pecha leaf; Mac shows live preview.  
2. **Capture** — grab a high-res still from the stream (canvas draw or `ImageCapture` when available).  
3. **Image QA (optional, pre-OCR)** — blur / crop / guide-overlay checks can reject a frame *before* OCR so you don’t burn seconds on an obviously bad shot. This is a retake *hint*, not the advance gate.  
4. **OCR** — BDRC + quality scorer (same thresholds / settings model as interactive OCR).  
5. **Decide on this page only**  
   - Accept → commit page, advance.  
   - Bad image or recoverable OCR fail → discard still, retake.  
   - Pathological → flag for human proofing, then continue.  
6. Repeat until the book is done → DOCX export (existing T-08 path once wired).

### Mapping onto existing architecture

Interactive OCR already thinks in per-page images under the job store (`jobs/<id>/page-NNN/image.png`, settings, attempts). Live capture should:

| Capture action | Job store action |
| -------------- | ---------------- |
| New page still | Write / replace `image.png` for page N |
| Retake | Replace image, clear or append attempt, re-run `run_page` |
| Accept | Finalize page, `N → N+1` |
| Escalate | Mark page for human proofing (existing accept / edit / retry actions) |

Product OCR today is PDF-only (`PDFUpload` accept `.pdf`). Image ingest and camera UI are new surfaces; the backend page model does not need reinventing.

---

## Continuity Camera notes

**What it is:** Apple feature that exposes the iPhone camera as a webcam on a nearby Mac (same Apple ID, Bluetooth + Wi‑Fi, Continuity enabled). Wired USB also works if the phone trusts the Mac. Used by FaceTime, Zoom, Photo Booth, and — with caveats — browser `getUserMedia`.

**Not the same as:** Continuity Camera *document import* (“Import from iPhone → Take Photo / Scan Documents” in Finder/Notes). That is a macOS native flow, not available to web apps the same way. This design targets **webcam Continuity Camera**.

**Browser caveats:**

- **Safari sees the iPhone and streams it. Chrome does not.** On this Mac, Chrome's device list was only "MacBook Air Camera" while Photo Booth and Safari both saw the phone. Do not block the spike on Chrome, and do not assume a Chrome product path until that changes.
- iPhone often needs the **“magic pose”** for browsers to see or stably stream it: landscape, screen off / locked, motionless (not handheld), camera unobstructed. Safari worked in that pose. The other conditions in § 3 were not tried.
- Photo Booth's preview is mirrored; the saved JPEG is not. Photo Booth caps stills at 1470×980. It is a bad capture surface for this spike.
- Device may enumerate but deliver **zero frames** in some Electron / packaged Chromium hosts missing `NSCameraUseContinuityCameraDeviceType`. Not what we hit: Chrome never listed the phone.
- Wireless Continuity Camera conflicts with AirPlay / Sidecar on the Mac.
- Only one Continuity Camera session at a time (one iPhone ↔ one Mac). Quit Photo Booth before opening the browser.

---

## Latency (honest)

Live OCR gate **will** make the session wait-bound: you hold the pecha on the current page until OCR returns.

- Autocapture and image QA only reduce **wasted** waits on bad frames. They do not remove the successful-page OCR cost.  
- Wall-clock for ~200 pages = `(per-page OCR time + human framing/retake time) × pages`, once measured. **Do not invent a number** — fill in after the spike (§ Spike results).  
- Revisit hybrid / async pipelines **only after** live gate feels too slow in a real multi-page sitting.

---

## Non-goals (this phase)

- Full interactive OCR UI (T-09) or production camera routes.  
- Mobile PWA capture *on the phone* (opposite direction from Continuity Camera).  
- Batch PDF upload changes or `combine_to_pdf` replacement.  
- Vision-model escalation for phone photos (the vision path is being removed; revisit only if BDRC + human proofing proves insufficient).  
- Ticketed product build plan — that comes after spike notes land.

---

## Spike checklist

**Purpose:** Learn Continuity Camera reliability, still quality vs BDRC needs, and per-page wait time in one sitting. Prefer the fastest throwaway surface (static HTML page or a local-only Next.js route). No product UI.

**Order:** § 0 first. Body prose on a straight, evenly lit leaf reads. The remaining miss is the model window clipping short lines, not a reason to start with crop / deskew / perspective or a capture UI.

### 0. One-leaf readability gate

- [x] Take a few stills of one pecha leaf. Photo Booth first, then Safari.
- [x] Run them through the BDRC models (Woodblock, Ume, and the rest).
- [x] Judge the output by eye against the leaf. Detail in [Spike notes](#spike-notes-2026-11-03).

**Notes:** Woodblock is the best of the five models on these leaves. Ume is much worse. Body prose (leaf 1, and line 4 of leaf 2) reads. Section-outline lines full of སྒྲུབ / སྒྲོལ do not, until a white margin is added before the scale. That margin is wired and not yet re-run on the full page.

| Still | Model | Readable? | Notes |
| ----- | ----- | --------- | ----- |
| leaf 1, Photo Booth 1470×980 | Woodblock | Body yes, after the top-rule clip | First line was soup until the frame stopped riding on the letters |
| leaf 2, same size | Woodblock | Outline lines no; line 4 yes | Same ink size and contrast as leaf 1. The text is the difference |
| leaf 2, Safari 1920×1440 wide | Woodblock | No better | Frame got bigger; glyphs stayed ~20–25px tall |
| leaf 2, Safari close | Woodblock | Worse | Taller glyphs, plus glare, skew, and a cut-off line |

**Prerequisites (§§ 1–6)**

- [ ] iPhone XR+ (iOS 16+), Mac (Ventura+), same Apple ID  
- [ ] Continuity Camera on: iPhone Settings → General → AirPlay & Continuity  
- [ ] Bluetooth + Wi‑Fi on; Mac not using AirPlay/Sidecar  
- [ ] Backend OCR models available if timing BDRC (`python scripts/download_models.py`)

### 1. Device enumeration

- [x] In **Safari** and **Chrome** on Mac, request camera permission and call `navigator.mediaDevices.enumerateDevices()`.
- [x] Confirm a `videoinput` whose label looks like the iPhone appears.
- [x] Open a stream with `{ video: { deviceId: { exact: … } } }` (not “default”, which may pick FaceTime HD).

**Notes:** Throwaway page `backend/spike/camera.html`, served at `http://localhost:8765/camera.html`. Quit Photo Booth first.

| Browser | iPhone listed? | Stream OK? |
| ------- | -------------- | ---------- |
| Safari  | yes | yes |
| Chrome  | no — only "MacBook Air Camera" | n/a |

### 2. Preview + still capture

- [x] Show live `<video>` preview from the Continuity Camera device. Safari only.
- [x] Capture a still (the page tries `ImageCapture.takePhoto()`, then canvas `drawImage` + JPEG). Which path ran was not written down.
- [x] Save locally. Files landed in `backend/spike/stills/` (gitignored).

**Notes:**

- Capture method used: Safari, throwaway page. Download name is `leaf-2-chrome.jpg` because the page hardcodes that name. The browser was Safari.
- Still dimensions (W×H): 1920×1440. Photo Booth comparison stills are 1470×980.
- File size / format: JPEG, ~680 KB for the wide Safari still.  

### 3. Magic-pose / failure modes

For each condition, note whether preview works, stream stalls, or device disappears:

| Condition | Result |
| --------- | ------ |
| Phone in magic pose (landscape, locked, stable) | Stream held for both sittings (~37 minutes, no drop-outs logged) |
| Phone handheld / moving | not tested |
| Phone screen on / unlocked | not tested |
| Bluetooth off | not tested |
| Wi‑Fi off | not tested |
| Mac AirPlay / Sidecar active | not tested |
| Device listed but zero video frames | not seen |

**Notes:** Safari listed the iPhone in both sittings, and its Desk View camera in the first. The harness logs camera events, so a drop-out in a later sitting shows up in `summary.md`. The other rows are only worth testing if a capture UI is ticketed.

### 4. Resolution / DPI vs pecha readability

BDRC in this repo is tuned around ~300 DPI PDF renders. Phone stills are resolution-in-pixels, not DPI — effective DPI depends on leaf size and camera distance.

- [x] Photograph one pecha leaf at desk distance and closer. No guide overlay yet.
- [x] Visually judge whether glyphs look sharp enough for OCR at that distance.
- [x] Record still dimensions. Physical leaf size was not measured.
- [x] Desk-distance guidance matters less than whether the line survives the model window. Upscaling a tight crop made the read worse.

**Notes:** On the Photo Booth pair, ink-band height was ~38px and contrast ~84 on both leaves. Leaf 2 failed anyway. A 1920×1440 Safari frame of the whole desk did not grow the glyphs (still 20–25px). A closer Safari frame reached 31–42px and the read got worse (glare, leaf not square, line cut off). The lever that moved སྒྲུབ was a white margin before the 3200×100 scale, not more pixels.

### 5. Latency baseline (live OCR gate)

Time one pecha-like page end-to-end:

1. Capture still  
2. Run BDRC OCR (CLI `ocr_assist` on a one-page PDF/image, or engine directly)  
3. Quality score  

| Metric | Value |
| ------ | ----- |
| Capture → still ready (ms) | not measured separately; included in capture → result |
| Still → OCR + score (ms) | 1700 median, 2200 p90 (Woodblock, second sitting) |
| Total gate wait (ms) | 2600 median, capture → result shown (second sitting, vote off the live path) |
| Subjective flip-rhythm feel (1–5) | not rated. Reading the result (8 s median) and framing take longer than OCR |

Rough 200-page projection: about 2.4 hours at the second sitting's 43 s median leaf to leaf, with retakes from the splitter bug included. The third sitting re-measures this with the fix.

**Notes:** Spellcheck in this run had no dictionary (`database_url` unset), so `unknown_word_ratio` was 0 and composite scores were generous. Leaf 1 Woodblock composite was 1.00 on structural errors alone.

### 6. Autocapture probe (optional)

- [ ] Overlay a pecha-shaped guide on the preview.  
- [ ] Detect frame stability over N consecutive frames (e.g. low motion / Laplacian variance above threshold).  
- [ ] Note false triggers (shadows, hands, turning the leaf).  
- [ ] Do **not** build product autocapture logic yet — record observations only.

**Notes:** _(fill in)_

---

## Spike results

As of 2026-11-18, after two sittings (20 sides, 47 captures) and the splitter fixes. § 3 is only partly run and § 6 (autocapture) not at all. Do not ticket a capture UI until the third sitting in [Pick up here](#pick-up-here-next-branch) is written down.

| Question | Answer |
| -------- | ------ |
| One-leaf stills readable by BDRC (§ 0)? | Body prose yes, with Woodblock. Section-outline lines read after the white margin before the scale |
| Continuity Camera reliable enough in Safari/Chrome? | Safari yes: no drop-outs in ~37 minutes of sittings. Chrome no — the iPhone is not in `enumerateDevices` |
| Still quality adequate for BDRC without heavy preprocess? | Yes for this pecha. Most bad reads came from the line splitter, now fixed; sharpness did not separate bad reads from good |
| Per-page wait acceptable for a 200-page sitting? | Likely: 2.6 s to the result, 43 s leaf to leaf, ~2.4 h per 200 sides before the splitter fix. Confirm in the third sitting |
| Does the quality gate catch bad frames? | Not alone. It passes partial reads at high scores. Gate plus a line-count check matched the human call on 29 of 32 captures in the second sitting |
| Autocapture worth pursuing next? | Not yet |
| Open questions / blockers | Retake rate with the splitter fix. Default model for photos (Woodblock) vs typeset PDFs (Modern). Whether the vote is worth it, scored by CER. Highlighter on a student's pecha. Chrome stays a documented no |

## Spike notes, 2026-11-03

Two leaves of one pecha. Stills are gitignored under `backend/spike/stills/`. Transcripts and line crops are under `backend/spike/out/`. Throwaway runners: `backend/spike/leaf_readability.py`, `backend/spike/first_line_crop.py`, `backend/spike/camera.html`.

### What the two leaves actually are

Leaf 1 is six lines of ordinary uchen prose. Woodblock scored composite 1.00 (structural-error ratio 0.009). It misses སྒྲུབ once, inside a line that otherwise reads.

Leaf 2 is a section opening. The curl at the start of line 1 is a **yig mgo** (the wave), then a shad. It is not a seed syllable. Lines 1–3 are an outline built out of སྒྲུབ, སྒྲོལ, and ཿ. Line 4 is plain prose (དབང་ཐོབ་ཅིང་དམ་ཚིག…) and reads cleanly in the same photo. Ink-band height and contrast match leaf 1 (~38px, contrast ~84). The page is harder because of the text, not because the photo is worse.

Cropping the yig mgo off line 1 does not fix the line. It only removes a garbage prefix.

### Top rule on line 1

`extract_line_images` used to let line 1 dilate to row 0, so the pecha's top rule sat on the letter heads and line 1 came out soup. The first fix (`first_line_top_bound`, clip a tenth of the line height above the contour) read leaf 1 line 1 as `དཀོན་མཆོག་མཆོད་པ། གསུང་རབ་བཀླག་པ།…` but broke both golden parity scans. Superseded on 2026-11-04, see below.

### Model window

Woodblock sees each line only after a fit to 3200×100 and an adaptive binarize. Leaf 1's lines are long, so width hits 3200 first and the glyphs sit in about 76 of the 100 rows, with room above and below. Leaf 2's lines are shorter, so height hits 100 first and the glyphs touch the top and bottom. The subscript is still in the binarized image. It is crushed against the edge.

Adding white above and below the extracted line, then OCRing that crop:

| Pad on a ~40px line | Leaf 2 line 2 | Leaf 2 line 3 | Leaf 1 line 2 |
| --- | --- | --- | --- |
| 0 | སླྲབ, སྐབ | སྒྲབ, སྐྲ | already clean |
| 4px | སྒྲུབ, སྒྲུབ | སྒྲུབ, སྐྲུབ | holds |
| 8px | སྒྲུབ, སྒྲུབ | སྒྲུབ, སྒྲུབ | འབར starts to drift |
| 12px+ | slips | ཆུབ becomes ཆུ་བོ | རྒྱུ becomes རྒྱ |

སྒྲོལ still comes out སྦྱོར. Four pixels is about a tenth of those line crops.

The table above is the saved line crops, padded by hand. The first version in code (a flat 10% pad on every line) broke tibetan-baseline. Superseded on 2026-11-04, see below.

### Considered and set aside

- **Woodblock-Stacks** (one symbol per stack, ~9,900 of them) does read སྒྲུབ on the outline lines. It turns line 1 into a run of Sanskrit stacks and nicks the clean line (དམ → དོམ). You cannot add symbols to Woodblock; its output layer is 83 Wylie letters.
- **Run both models and keep the better line.** Rejected on 11-03. **Reopened 2026-11-05:** Woodblock, Modern and Woodblock-Stacks make different errors (Modern reads stacks better; Woodblock keeps vowels and tshegs), so `backend/spike/ensemble.py` votes over each disagreement region with Woodblock as pivot. Decide on character and syllable error rates against the hand transcriptions. Ume_Druma and Ume_Petsuk are out of scope.
- **A substitution list** (སྐབ་ཐབས → སྒྲུབ་ཐབས). Rejected. It would also rewrite a real སྐབ.
- **Retraining.** Out of scope for the spike.
- **Just get closer, or upscale.** A closer frame without square, even light made the read worse. 2× cubic on a tight crop made it worse.
- **Blunt crop of the whole leaf** to drop the frame and side titles. Ate the tops of letters and still left a scrap of frame.

## Spike notes, 2026-11-04

The 11-03 working tree failed 8 of 17 tests in `tests/test_ocr_parity.py`. Both changes regressed the golden scans independently. Golden scans are the yardstick: tibetan-baseline (834 characters, base edit distance 31). menla's transcription does not line up with its page closely enough to score by edit distance (base 178), so for menla only the parity tests count.

### Why the 11-03 fixes broke the scans

- **Line-1 clip.** On the scans, gi-gu and na-ro on line 1 sit ~20px above the detected contour. A pad of `h // 10` (4px) cut them off. Worse, `extract_line_images` carries line 1's adapted `k_factor` to every later line, so changing line 1's bounds re-cut lines 2–7 too.
- **Flat margin.** Golden crops include dilation slack (up to 3–4× the contour height), so a 10% pad fired on every line. The pad also ran before `_pre_pad`, whose side patches are as wide as the line is tall, so every line shrank horizontally too.

### What replaced them

- **`whiten_rule_above`** (`BDRC/line_detection.py`). Finds the lowest horizontal rule above line 1: a row where dark runs at least a quarter of the line wide cover half its span. It paints everything down to that rule white, then crops line 1 as before, so bounds and `k_factor` are untouched. It catches the thin gray photo rules (leaf 1 at −87px, leaf 2 at −12px right on the letter heads) and the solid double rule on the scans. Pages without a rule are not touched.
- **`add_vertical_margin`** (`BDRC/Inference.py`), after `_pre_pad`. Pads only when the line's ink would fill more than 95% of the 100-row window, and pads back to 83% (about 4px on a 40px crop, matching the table above). Crops narrower than 6× their height are stray marks and are skipped. Measured ink fill: golden lines 80–95%, leaf 1 86–92%, leaf 2 100%. A 90% trigger padded menla line 4 and dropped Sanskrit marks (ཛྱཾ → ཛྱ, བྷཱ → བྷ).

### Results

- **Golden scans, through `extract_pdf`:** edit distance unchanged with each change alone and both together (tibetan-baseline 31, menla 178). The margin changes no golden line.
- **Leaf 1 (Woodblock):** byte-identical to the 11-03 transcript.
- **Leaf 2 (Woodblock):** སྒྲུབ now reads correctly 3 times (was སྐབ), and སྦྱོར, ལྟར, བྱང་ཆུབ, ཐུན་མོང, བསྙེན, and དུ are fixed. Still wrong: one བསྙེན་སྐྲབ, a new པ → པོ, and the yig mgo still garbles the start of line 1.
- **Parity: 15 of 17, now 17 of 17 after the allowlist change below.** On menla, whitening changes line 1's misread HUM from `ཧ-H` to `ཧར-MH`. The edit distance is the same, but the new read adds an `invalid_post_suffix` error type, which fails the two error-type tests. The crop is cleaner (rule gone, HUM intact). This needs a decision: accept the artefact in the golden allowlist, or gate the whitening.

### 2026-11-05: line 1 on leaf 1

The 11-04 result "leaf 1 byte-identical to 11-03" was misleading: the 11-03 transcript predates the clip, so line 1 was garbled in both. Whitening never fired on leaf 1 (its rule is 80px up, outside the crop). The real cause was ~40 rows of blank paper above a 25px line, which shrank it in the model window. `first_line_top_bound` now re-cuts line 1 with its top one median line gap above the box, at the `k_factor` it already adapted to, so later lines do not move.

| Reach (median gaps) | Leaf 1 line 1 | Leaf 2 line 1 | tibetan-baseline edit distance | menla edit distance |
| --- | --- | --- | --- | --- |
| off | garbage | garbage | 31 | 178 |
| 0.5 | reads | partial | 28 | 181 |
| **1.0** | reads (`དཀོན་མཆོག་མཆོད་པ།…`) | `…ཐབས་ཀྱི་རྩུ་ཐོ་ལས།གཞུང་དངོས་…` | 30 | 178 |
| 1.5 | worse | worse | 31 | 178 |

No later line changed at any reach. Median half-gap on the scans is ~30px against vowel marks at −20px; on the leaves the full gap is ~19px.

**Encoding sensitivity.** Re-encoding the same still (PNG lossless, JPEG q95–q50) flips 2–5 lines per leaf, mostly between near-equal readings (སྐྲབ↔སྒྲབ, ར་བ↔རབ, པོ↔པ), some better and some worse. The reads sit near decision boundaries on photos. Score encoding choices against the hand transcriptions, not by how many lines changed.

11-03 transcripts are kept in `backend/spike/out/baseline-2026-11-03/`, because `spike/leaf_readability.py` overwrites `out/`.

### Working tree at the time (since merged in #80)

- `BDRC/line_detection.py`: `rule_bottom_above`, `whiten_rule_above`
- `BDRC/Inference.py`: `add_vertical_margin`, called from `OCRInference.run` after `_pre_pad`
- `BDRC/UPSTREAM.md`: notes so both survive a vendor sync
- `backend/tests/test_line_extraction.py`, `backend/tests/test_line_margin.py`
- `backend/spike/`: throwaway page and runners. Stills and `out/` are gitignored
- This doc, and `.gitignore`

### Continue here

1. ~~Decide the menla HUM artefact.~~ Accepted 2026-11-04: `invalid_post_suffix` added to menla's golden allowlist. Parity is green.
2. ~~Score leaf 2 against a hand transcription.~~ Done 2026-11-05. Both leaves are hand-corrected (`backend/spike/transcripts/`) and are golden fixtures (`pecha-photo-leaf1-prose`, `pecha-photo-leaf2-section-opening`).
3. ~~Run a real sitting with the harness.~~ Two sittings done 2026-11-13 (see below). Smoke test on the two leaf stills beforehand: the gate accepted leaf 2 even though Woodblock gets 5% of its characters wrong. How to run the harness is in [Pick up here](#pick-up-here-next-branch).
4. Do not start capture UI, image ingest, or autocapture until the sitting is written down. Chrome stays a documented no.

### 2026-11-05: three-model vote

Woodblock, Modern and Woodblock-Stacks make different errors, so `backend/spike/ensemble.py` reads with all three and votes. Scored against the hand transcriptions:

| Reading | Leaf 1 CER / syllable ER | Leaf 2 CER / syllable ER |
| --- | --- | --- |
| Woodblock (production today) | 2.2% / 7.1% | 5.1% / 13.4% |
| Modern | 3.3% / 11.8% | 2.8% / 9.8% |
| Stacks | 1.8% / 4.7% | 7.6% / 12.5% |
| Vote, Modern pivot, no dictionary | 1.2% / 3.8% | 2.8% / 8.9% |

The best single model changes per page. The configuration tuned on leaf 1 (Stacks pivot plus dictionary tie-break, 0.7% / 2.4%) did not hold up on leaf 2 (4.9% / 8.9%). Modern-pivot voting without a dictionary is best or near-best on both. Dictionary-aware reading is deferred until there is a hosting decision. Details, ideas, and what each option changes for golden tests and CI: [OCR_ENSEMBLE_AND_DICTIONARY.md](OCR_ENSEMBLE_AND_DICTIONARY.md).

## Spike notes, 2026-11-13: first sitting

Five sides of one pecha (printed folios 143–145), 18.7 minutes, 15 captures. Log and stills: `backend/spike/sittings/20261113-110402/` (gitignored). The leaf filled about a quarter of the 1920×1440 frame's height. Safari listed the iPhone and its Desk View camera; the stream never dropped.

| Measure | Value |
| --- | --- |
| OCR (Woodblock, server) | 1.5 s median, 1.8 s p90 |
| Capture → result shown | 4.9 s median, of which 3.3 s was the inline vote |
| Result → decision (reading the output) | 20 s median, 32 s p90 |
| Leaf to leaf | 60 s median, 129 s p90 (n = 4) |
| Retakes | 6 for 5 leaves; 3 leaves needed more than one attempt |

At the median pace a 200-leaf book is about 3.3 hours. OCR is not the slow part; reading the output to decide is.

**The gate does not catch partial reads.** It accepted 9 of the 11 frames that were retaken or flagged, including one-line reads at composite 1.00. The composite scores only the text that was read. Leaf 145 (attempt 3, highlighter on most lines) read 2 of 7 lines and passed at 0.98. Leaf 144, attempt 3, which was accepted, read 6 of 7 lines; nobody noticed at the time. Line count against the leaf's usual count would have caught both. The title leaf (1 line) and the opening leaf (4 lines) read completely, so a short count is a prompt to look, not a reject.

**The vote is not worth the wait on the live path.** It beat Woodblock's composite on 3 of 15 captures and turned the highlighted leaf into garbage that still scored 0.81 (no dictionary, so the scorer cannot tell). Composite is not CER, so this does not overturn the 11-05 table; it only means the vote should not block capture.

**Highlighter** on a student's pecha is a failure mode the two test leaves did not have. Leaf 145 lost lines to it on every attempt.

**The retakes were partly the harness.** Space could be pressed again before deciding, and a repeat capture overwrote the still with the same name (leaf 1: 6 captures, 3 files kept). Keyboard-only controls were also confusing.

### Harness changes after the sitting

- The page is restyled on the spellcheck page (same palette, Jomolhari, red / yellow spelling underlines) and stacked: photo, verdict, numbered lines, then Accept / Retake / Flag buttons. No keyboard shortcuts. Capture is disabled until the last capture is decided.
- A line check: "Lines on a full leaf" is sent with each capture, logged as `expected_lines` / `lines_short`, and shown as "Only 6 of 7 lines read". The summary adds a "Gate plus line check vs you" table.
- The vote runs in a background thread after the result is returned and is logged as a separate `vote` event. A capture that has to wait for it logs `queue_ms`.
- Stills never overwrite: a repeated page and attempt gets a `-2` suffix.

### Next

1. Second sitting, 20+ leaves, with the line check on. Leave notes on retakes.
2. If the line check matches your calls, make it part of the gate (`decide`) for photo pages.
3. Score the vote by CER on more hand-transcribed leaves before putting it back on any live path.

### Ideas from the sitting (not yet built)

- **Read the folio number from the leaf.** The harness counts leaves from a number you type, so a skipped or repeated leaf shifts every later number. To go back to the hard copy you need the printed folio. These leaves carry it in both margins: Arabic numerals on the right (143, 144, 145) and the side title with the Tibetan folio on the left. Line detection drops the margins today, so this needs its own crop and read. Front and back of a leaf share a number (143 was both the title side and the next side), so the record needs folio plus side.
- **Fix small things during capture.** Built 2026-11-14: tap a line to edit, Remove for stray lines, flags shown as red / yellow highlights with a count per line. Edits are logged as `final_lines`, `edits` and `removed` on the decision; the capture record keeps the OCR reading. Editing a syllable in the reading before accepting would save a trip to `/ocr-assist` for one-character misreads. The edit should be logged next to the original read so the sitting still measures OCR accuracy.
- **Retake in one click.** Built 2026-11-14: the preview stays live during review, and Retake now logs the retake and captures. Today it is Retake, then Capture again. Instead, show the live preview beside the review and let "Capture again" both log the retake and take the new still.

## Spike notes, 2026-11-13: second sitting

Fifteen sides with the restyled page and the line check, 18.3 minutes, 32 captures. Log and stills: `backend/spike/sittings/20261113-151832/` (gitignored). Lines on a full leaf was 7, then 5, then 6 (most of this section has 6).

| Measure | Value |
| --- | --- |
| OCR (Woodblock, server) | 1.7 s median, 2.2 s p90 |
| Capture → result shown | 2.6 s median (was 4.9 s with the vote inline) |
| Result → decision | 8.3 s median (was 20 s), 34 s p90 |
| Leaf to leaf | 43 s median, 123 s p90 (n = 14) |
| Retakes | 17 for 15 sides; 8 sides needed more than one attempt |

200 sides at the median pace: about 2.4 hours.

**Gate vs line check.** Every `escalate` was a partial read, and the gate never escalated a full one. With the line check, 13 of 14 non-short reads were accepted, and 16 of 18 short reads were retaken. The two short reads accepted were the title side (2 of 7) and the opening side (4 of 7), which really have fewer lines.

**Most retakes were caused by the line splitter, not the framing.** On this pecha the line detector merges all six lines into three pairs (78–82 px; a single line is ~40 px). `split_tall_lines` only tried to split lines taller than 1.5× the median height, and the median was set by the pairs. Reads only came out whole when one or two noise specks (4–13 px "lines") happened to pull the median down. Photos of the same side that look identical read 4 lines of garbage or 6 clean lines depending on the specks. Sharpness (Laplacian variance) did not separate short reads from full ones.

**Fix:** `split_tall_lines` now runs the valley test on every line, since the test already requires a waist in the line mask that a single line does not have. Re-reading all 32 captures: all 16 short reads of 6-line sides now read 6 lines (two read 7 because the opening ༄ is detected as its own line), and no full read changed. Leaf 9's worst capture now reads within 94% of its good capture. Parity, line extraction and margin tests: 40 of 40 pass, golden scans and both photo leaves included. Recorded in `BDRC/UPSTREAM.md`. This runs in production too.

**Follow-up, 2026-11-17:** splitting every line also cut single lines of a clean scan (Gyudsum Kongwa PDF) at the waist above their hanging vowels, leaving the line without its bottom and the vowels as a near-empty sliver. Cuts that would leave a stripe peaking under 0.08 of the line's peak are now dropped. Re-reading all 47 sitting stills: 46 identical, one lost a 4 px junk line. Real stripes in the photos peak at ≥ 0.09, the scan's slivers at ≤ 0.05, so the margin is thin; add photo stills near it to the goldens if the threshold is ever moved.

Two more findings from the same PDF:

- **Model.** Woodblock drops ུ under stacks and reads ༔ as ཿ on typeset text. Modern flags 6.0% of syllables across the 8 pages against Woodblock's 10.8% (Woodblock-Stacks 12%, the Ume models 31–36%). The sitting page now has a model picker; opening a PDF switches it to Modern, and "Read again" re-reads a PDF page with the picked model (logged as `reread`, not a retake).
- **Fragments.** Specks and vowel tails detected as their own "lines" set the crop bound of the real line beside them, cutting off its bottom. Detections under 0.6× the median line height no longer bound a neighbour's crop. Replaying the 49 camera stills and the 8 PDF pages under both Woodblock and Modern: nothing got more flags; the PDF pages lost up to two thirds of theirs (p4 12 → 5, p5 14 → 4 with Modern). One still (2026-11-13 page 7 a2) changed text with the same flag count. Dropping fragments from the line list instead made three stills worse, because the adapted `k_factor` is carried line to line.

Next steps moved to [Pick up here](#pick-up-here-next-branch).

---

## Pick up here (next branch)

Where things stand on 2026-11-18: the harness, both sittings' write-ups, and the line-splitting fixes are on `main` (0.9.0). The splitter fixes also run on the live site's scanned-PDF spellcheck. The open question for the spike has not changed: **ticket a capture UI or not**. One more sitting is needed to answer it.

### Setup

- Branch off `main`, e.g. `spike/capture-third-sitting`. Keep #79 open and reference it from the PR.
- Sitting logs and stills are gitignored and exist only on the machine that ran them: `backend/spike/sittings/20261113-110402/` (first sitting), `20261113-151832/` (second), and the 2026-11-16 / 11-17 folders (PDF reads and replays). Tables in this doc are copied from their `summary.md`. Re-reading old stills after a pipeline change needs these folders, so do not delete them.
- `cd backend && python scripts/download_models.py` once, if the models are missing.
- `docker compose up -d postgres` before a sitting so the word corpus marks misspellings. The page warns when it is off.

### Running the harness

- `cd backend && venv/bin/python -m spike.sitting_server`, then open http://127.0.0.1:8765 in Safari (not `localhost`, which can resolve to another server on `::1`). Add `--vote` to run the three-model vote in the background; it is logged as a separate event and does not block capture.
- Connect the camera, set "Lines on a full leaf", then Capture. Under the reading: tap a line to fix it, Remove a stray line, then Accept, Retake now, or Flag for proofing. The model picker switches models; Read again re-reads a PDF page.
- No camera: **Open a PDF**. Pages are imaged as OCR Assist images them (embedded scan at native size, else 300 DPI) and logged as `pdf.native` or `pdf.render300`. Opening a PDF switches the model to Modern.
- Everything goes to `backend/spike/sittings/<started-at>/log.jsonl`, with the stills beside it.
- Afterwards: `venv/bin/python -m spike.summarize_sitting spike/sittings/<started-at>` (from `backend/`) writes `summary.md` (retakes, latency, gate vs you, gate plus line check vs you, fixes, camera) and `transcript.txt`.
- Local only: binds 127.0.0.1, nothing in `app/` imports `spike/`, and `spike/` is excluded from the production image (`backend/.dockerignore`). Keep it that way.

### Steps, in order

1. **Third sitting, 20+ sides, with the splitter fixes.** Same pecha as the second sitting if possible, so retakes compare. Leave a note on each retake saying why. Done when: `summary.md` is written up here as "Spike notes, <date>: third sitting", with the retake rate, leaf-to-leaf time, and 200-side projection next to the second sitting's.
   - Expect far fewer retakes. What remains is the real framing rate.
   - If a retake is a pipeline bug (lines merged, cut, or lost) rather than framing, fix it on this branch the way the splitter was fixed: replay all sitting stills before and after, and add a golden if a threshold moves. `SLIVER_PEAK_RATIO` (0.08) has a thin margin; see the 2026-11-17 follow-up above.
2. **Line check in the gate.** If the third sitting confirms that gate plus line check matches your calls, add the line-count check to `quality.decide` for photo pages (`app/ocr_assist/quality.py`), with tests. This is product code and ships, so it needs its own commit and a CHANGELOG line. Done when: the summary's "gate plus line check vs you" table matches the human call on nearly every capture, and the check lives in `decide`, not only in the harness.
3. **Decide: ticket a capture UI or not.** Write the decision and reasons at the top of this doc and update **Status**. If yes, write the ticket against the slimmed `/ocr-assist` job store (see [Mapping onto existing architecture](#mapping-onto-existing-architecture)); it stays behind `OCR_ASSIST_LOCAL`. If no, write down what would change the answer.

### Optional, only if they block the decision

- **Folio from the leaf.** See the idea in the first sitting's notes. `find_folio_marker_end()` in `BDRC/line_detection.py` already separates the folio annotation from body text and may be a starting point.
- **Score the vote by CER** on more hand-transcribed leaves (`backend/spike/transcripts/`) before putting it on any live path.
- **Highlighter.** Lines under highlighter were lost on every attempt in the first sitting. Note how often it comes up; don't fix it yet.

### Not in this branch

- Removing the diagnostician and vision code: [CODE_REVIEW_FIXES.md](CODE_REVIEW_FIXES.md) Track B1, its own branch. A capture UI ticket depends on it; the third sitting does not.
- Capture UI, image ingest, autocapture, Chrome support.

---

## Relationship to interactive OCR plan

- Extends **Physical-book photos** under Future / not yet ticketed in [INTERACTIVE_OCR_PLAN.md](INTERACTIVE_OCR_PLAN.md).  
- Depends conceptually on job store + per-page settings + quality scorer (already implemented).  
- Product capture UI should stay **local-only / behind-flag** (`OCR_ASSIST_LOCAL`) — same deployment posture as the slimmed `/ocr-assist` proofing page.
