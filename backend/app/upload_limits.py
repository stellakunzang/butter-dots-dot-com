"""PDF upload caps.

Spellcheck is the public API. OCR assist is local-only and keeps a higher
byte cap for book-sized scans. Both reject an oversize body with HTTP 413.
"""

SPELLCHECK_MAX_UPLOAD_BYTES = 50 * 1024 * 1024
# A hard stop so one PDF cannot queue unbounded render/OCR work.
# A typical pecha sits well under this.
SPELLCHECK_MAX_PAGES = 500
OCR_ASSIST_MAX_UPLOAD_BYTES = 100 * 1024 * 1024
