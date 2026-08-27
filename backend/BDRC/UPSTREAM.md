# BDRC vendor sync

This directory is vendored from [`buda-base/tibetan-ocr-app`](https://github.com/buda-base/tibetan-ocr-app) (MIT). The OCR pipeline lives upstream as a PySide6 desktop app; we re-use just the `BDRC/` package for server-side OCR.

## Last sync

- **Upstream repo path:** `../tibetan-ocr-app`
- **Upstream HEAD SHA at sync time:** `62d68ec01996560e1105796630c10489731fe8aa`
- **Upstream state ported:** working-tree state (HEAD + uncommitted WIP). The upstream WIP was substantially ahead of HEAD on the files we sync; per the user, the WIP is the desired state for this port.
- **Synced on:** 2026-05-19
- **Ticket:** T-01 of the [interactive OCR plan](../../docs/planning/INTERACTIVE_OCR_PLAN.md#t-01--port-ocr-engine-improvements-from-tibetan-ocr-app)

## Fixes cherry-picked in this sync

### `line_detection.py`
- Rotation-angle sign fix in `get_rotation_angle_from_lines` and `calculate_rotation_angle_from_lines`: `abs()` applied to both low- and high-angle filters, and the high-angle formula corrected from `-(90 - mean)` to `90 + mean`. Modern OpenCV returns angles in `[-90°, 0°)`, so near-90° tilts come back negative — the old form lost the sign.
- `max_angle` lowered from 5.0° to 2.0° to reject implausibly large rotations.
- `filter_line_contours`: width threshold relaxed from 0.01 to 0.005, height floor from 10 to 3, and now logs why everything was rejected when zero contours pass.
- New `split_tall_contours()` + `split_tall_lines()` to break apart contours that span multiple text rows (a recurring failure mode where pixel bridges merge adjacent lines).
- New `_find_valley_rows()` helper for the above.
- New `find_folio_marker_end()` for separating the folio-number annotation from body text in Tibetan folios.
- New `filter_outlier_lines()` to drop isolated page-border detections that aren't real text.
- `extract_line` / `get_line_image` / `extract_line_images`: optional `y_bounds` parameter clips the dilated mask to the midpoint of neighboring lines, preventing bleed.
- `sort_lines_by_threshold2` now runs `split_tall_lines` and `filter_outlier_lines` on the grouped output.

### `image_dewarping.py`
- Collinearity check before TPS solve: if y-centers of the slice-centroids are near-linear (pure tilt rather than curvature), skip TPS — the kernel would be singular and divide-by-zero. Pure tilt is handled by rotation upstream of this anyway.
- `npt.NDArray(...)` → `np.array(...)`: `npt.NDArray` is a type-hint alias, not a constructor; the old form crashed when actually called.
- Removed a duplicate `corners *= [height, width]` (typo).
- Local mod: kept this repo's `try/except ImportError` guard around `from tps import ThinPlateSpline`. Upstream removed it; `tps` is not in our `requirements.txt` and the TPS code path is gated by `use_tps=False` in `app/pdf/ocr.py`, so the guard preserves importability.

### `Inference.py`
- `update_line_detection`: now also reassigns `self.line_config = config` after swapping the inference instance. Previous version updated the inference object but kept the stale config, so subsequent runs would misuse the old shape.
- TPS dewarp path wrapped in `try`/`except` with a non-finite-values guard; on failure, falls back to non-dewarped extraction instead of crashing the whole page.
- Encoding conversion wrapped in `try`/`except`; conversion failures keep the raw OCR output instead of dropping the line.
- Early return on degenerate line images (`shape < 2`).
- Diagnostic prints (`[Diag]`, `[TPS]`, `[OCR]`) for blank-page and dewarp-failure debugging.
- Type annotations migrated from PEP 604 `A | B` to `Union[A, B]` (no behavior change; broader Python compatibility).

### `Runner.py` (no `Runner.py` in this repo — equivalent logic added elsewhere)
The upstream `Runner.py` is a Qt `QRunnable` wired to PySide6 signals; nothing to port directly. The reusable bit — explicit multi-channel image handling before calling the pipeline — was added as `_normalize_to_bgr()` in `backend/app/pdf/ocr.py` and called inside `BDRCOCREngine.run_on_image`. It handles grayscale, BGRA, and exotic (e.g. CMYK+Alpha) inputs.

## How to re-sync next time

1. `cd ../tibetan-ocr-app && git rev-parse HEAD` — record the new upstream SHA.
2. `diff -u backend/BDRC/<file>.py ../tibetan-ocr-app/BDRC/<file>.py` per file, port the deltas.
3. Preserve any local mods listed above (currently: the `tps` import guard in `image_dewarping.py`).
4. Update this file with the new SHA, date, and any new fixes pulled forward.
