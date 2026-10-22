# OCR assist CLI

Local only. Set `OCR_ASSIST_LOCAL=true` in `backend/.env`. The routes are
refused on Render, and nothing in the public nav links to `/ocr-assist`.

The commands below are the current CLI. It still auto-accepts pages and can
call the diagnostician and vision compare. That loop is being removed. See
[CODE_REVIEW_FIXES.md](../planning/CODE_REVIEW_FIXES.md) Track B. Do not treat
this page as the product description.

## Run

```bash
cd backend
source venv/bin/activate
python scripts/download_models.py   # one-time
venv/bin/python -m app.ocr_assist.run_job /path/to/book.pdf \
  --jobs-root ./jobs \
  --model Woodblock \
  -v
```

Jobs land in `backend/jobs/` (gitignored). The run prints the job id and the
`output.docx` path. On macOS, `--open` opens that DOCX and `--reveal` shows
the job folder in Finder.

```text
jobs/<job_id>/
  manifest.json
  output.docx
  page-001/
    image.png
    settings.json
    attempts/01/ocr.txt
    attempts/01/quality.json
    attempts/01/spellcheck.json
    final.txt
```

A page subset, or a re-run of one page of an existing job:

```bash
venv/bin/python -m app.ocr_assist.run_job /path/to/book.pdf \
  --jobs-root ./jobs --pages 3,7,12 -v

venv/bin/python -m app.ocr_assist.run_job \
  --jobs-root ./jobs \
  --job-id <job_id> \
  --rerun-pages 7 \
  -v
```

Other flags: `--max-attempts`, `--threshold-accept`, `--threshold-reject`,
`--model`.

`--enable-ai` turns on the diagnostician. It needs `ANTHROPIC_API_KEY`.
Gemini compare needs `GEMINI_API_KEY`. Both are optional and off by default.

The browser UI is http://localhost:3000/ocr-assist when the backend flag is
on.
