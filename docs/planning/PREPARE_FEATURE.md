# "Prepare" — Document Conversion & Style Guide Feature

Convert PDFs, DOCX, and RTF files into properly styled, editable documents
that follow the community's typography conventions for Tibetan sadhana texts.

---

## Problem statement

The community regularly needs to update sadhana texts — add a lineage holder's
name, correct a line, update an aspiration — but the only available artifact is
a PDF or a DOCX/RTF supplied by a previous formatter that has incorrect fonts
or no named styles. The workflow is:

1. Obtain source document (PDF, DOCX, or RTF)
2. Produce an editable file (Pages, Word, Google Docs) with correct styles
3. Make editorial changes
4. Export back to PDF for printing/distribution

Step 2 is currently manual and error-prone. The goal of this feature is to
automate it reliably.

---

## Source of truth

The calibration fixture for this feature is the **final Pages-exported PDF**
with styles correctly applied. That document (not any RTF or earlier DOCX) is
the ground truth for:

- Which font names are in use
- What font sizes map to which style roles
- Which text is colored (e.g., red for certain syllables)

The RTFs and DOCXs from the previous formatter are explicitly **not** source of
truth — they have inconsistent fonts and no named styles.

---

## Named styles

The community's documents use these style roles:

| Style name             | Script   | Notes                                      |
|------------------------|----------|--------------------------------------------|
| Tibetan Title          | Tibetan  | Largest Tibetan text on the page           |
| English Title          | Latin    | Largest English text on the page           |
| Tibetan Body           | Tibetan  | Main prayer / liturgical content           |
| English Body           | Latin    | Main English prose                         |
| English Transliteration| Latin    | Phonetic rendering; typically italic       |
| Tibetan Yig Chung      | Tibetan  | Smaller Tibetan (instructions, captions)   |
| English Yig Chung      | Latin    | Smaller English (rubrics, stage directions)|
| Colored (red)          | Either   | Mantra syllables or emphasis; color preserved |

These become named paragraph styles in the output DOCX, which Pages, Word,
and Google Docs all respect on import.

---

## UI

### Tab name

**"Prepare"** — short, purposeful, not technical. Secondary option: "Convert."

### Flow

```
Upload a document
  [drag-and-drop zone: PDF · DOCX · RTF]

    ↓ file selected

Detection summary (shown before download):
  "Detected: 4 style types · Tibetan + English · 12 pages"
  Optional: table preview — style / font / sample text

Output format:
  [● DOCX]  [○ PDF]

  [Prepare document →]

    ↓ processing (seconds for digital, longer if OCR fallback)

Download:
  [Prepared DOCX ↓]
  Note: requires [FontName] to be installed on your device.
```

Showing a detection summary before download is important: it lets the user
catch a mis-classified section or an unrecognized font before they open the
file in a word processor.

---

## Architecture

```
Upload (PDF / DOCX / RTF)
       │
       ▼
  Normalize to fitz-readable PDF
  ├── PDF: open directly
  ├── DOCX: read via python-docx (preserves run metadata without conversion)
  └── RTF: LibreOffice --headless → PDF (one CLI call in Docker)
       │
       ▼
  fitz get_text("rawdict")
  Per span: text · font name · font size · color · bbox · flags (bold/italic)
       │
       ▼
  Style Classifier (heuristic rule table)
  ├── Script detection: Tibetan (U+0F00–U+0FFF) vs Latin
  ├── Size buckets: largest → Title, mid → Body, smallest → Yig Chung
  ├── Italic flag → English Transliteration
  └── Color (non-black) → Colored run
       │
       ▼
  DOCX Builder (python-docx)
  ├── Named paragraph styles applied per classified block
  ├── Font name + size set per run
  └── Run color preserved for red/colored text
       │
       ▼
  Download DOCX
```

For DOCX input, `python-docx` reads run-level font/size/color/bold/italic
directly — no conversion to PDF needed. This is the better path for DOCX
because it skips any rendering step.

---

## What is already in place

| Component | Where |
|---|---|
| fitz text extraction with font metadata | `backend/app/pdf/extractor.py` |
| python-docx DOCX generation | `backend/app/pdf/docx_exporter.py` |
| FastAPI file upload pattern | `backend/app/api/spellcheck.py` |
| Docker container with PyMuPDF | `backend/Dockerfile` |

---

## What needs to be built

### Backend

- `backend/app/convert/` — new module
  - `normalizer.py` — routes input to the right extraction path
  - `extractor.py` — fitz rawdict extraction; DOCX run extraction via python-docx
  - `classifier.py` — heuristic style assignment rules (calibrated against the reference PDF)
  - `builder.py` — DOCX construction with named styles
- `backend/app/api/convert.py` — new endpoint: `POST /api/v1/convert/upload`
- LibreOffice headless in Docker image (for RTF input; adds ~300 MB to image)

### Frontend

- `frontend/pages/prepare.tsx`
- Nav link in Layout
- Detection summary component (show classified styles before download)

---

## Font handling note

DOCX does not embed fonts. The output file will reference font names (e.g.,
Jomolhari, Palatino) by name. Recipients must have those fonts installed.
The download dialog should list required fonts and link to where to get them.

A future improvement would be offering a PDF output alongside the DOCX for
recipients who don't have the fonts, using the embedded fonts from the source.

---

## Open questions before starting

1. **Reference PDF**: The final Pages-exported PDF needs to be uploaded as a
   fixture so the classifier can be calibrated. Without it, size-to-style
   mappings are guesses.

2. **RTF scope**: Is RTF input needed at v1, or can the first version support
   PDF and DOCX only? LibreOffice adds ~300 MB to the Docker image. Could be
   deferred to v2.

3. **Google Docs**: A DOCX with standard named styles imports into Google Docs
   reasonably well. There is no direct export to Google Drive without the Drive
   API. "Download DOCX, import to Docs" is the v1 answer.

4. **Font name portability**: If the source PDF uses a font the recipient does
   not have, the DOCX will fall back to a system font. Should we maintain a
   mapping of community-approved fonts and their fallbacks?

5. **Minimum viable classifier accuracy**: What is acceptable? If the tool
   gets 95% of lines right and 5% need manual style correction, is that useful
   enough to ship?

---

## Related work

- `tinkering/extract_tara_prayer.py` — proof of concept for fitz dict extraction
- `tinkering/recreate_tara_prayer_v2.py` — reconstruction attempt (used ReportLab, not DOCX; fonts wrong)
- `tinkering/RTF_CONVERSION_README.md` — documents the RTF → DOCX conversion problem and why MS Himalaya was tried
- `tinkering/Yumka 2024 ver 3.0 (Pages - For Review).pdf` — candidate reference PDF
