## What's in here

<!-- Describe the change and why it was made. -->

## Checklist

- [ ] `CHANGELOG.md` updated (new version section, or `[Unreleased]` only if shipping later)
- [ ] Tests added or updated where relevant
- [ ] No new console warnings or TypeScript errors

## How tested

<!-- Say what you ran. Delete lines that do not apply. -->

- [ ] `cd backend && venv/bin/pytest -m "not slow"`
- [ ] `cd frontend && yarn test:ci`
- [ ] If `backend/BDRC/`, `backend/app/pdf/`, or the OCR models changed:
      `cd backend && venv/bin/pytest tests/test_ocr_parity.py`
- [ ] If a page changed, what you clicked through in the browser:
