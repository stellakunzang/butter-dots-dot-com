# Error Tracking & PDF Annotation Architecture

## Complete Flow: Upload → Check → Annotate → Return

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USER UPLOADS PDF                                             │
│    - File: "tibetan_text.pdf"                                   │
│    - Size: 2.5 MB                                               │
│    - Pages: 10                                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. BACKEND: PDF TEXT EXTRACTION (Task 13)                       │
│    ┌─────────────────────────────────────────────────────────┐  │
│    │ OCR / PDF Parser extracts:                              │  │
│    │                                                          │  │
│    │ {                                                        │  │
│    │   "page": 1,                                             │  │
│    │   "text": "བོད་ཀྱི་སྐད་ཡིག་",                           │  │
│    │   "bounding_boxes": [                                    │  │
│    │     {"word": "བོད", "x": 100, "y": 200, "w": 50, "h": 20}, │
│    │     {"word": "ཀྱི", "x": 155, "y": 200, "w": 45, "h": 20}, │
│    │     {"word": "སྐད", "x": 205, "y": 200, "w": 48, "h": 20}, │
│    │     {"word": "ཡིག", "x": 258, "y": 200, "w": 45, "h": 20}  │
│    │   ]                                                      │  │
│    │ }                                                        │  │
│    └─────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. SPELL CHECK ENGINE (What we're building now - Tasks 4-6)     │
│    ┌─────────────────────────────────────────────────────────┐  │
│    │ Input: "བོད་ཀྱི་སྐད་ཡིག་"                                │  │
│    │                                                          │  │
│    │ Process:                                                 │  │
│    │ 1. Normalize Unicode                                     │  │
│    │ 2. Split into syllables: ["བོད", "ཀྱི", "སྐད", "ཡིག"]   │  │
│    │ 3. Check each syllable against rules                     │  │
│    │                                                          │  │
│    │ Output (Error List):                                     │  │
│    │ [                                                        │  │
│    │   {                                                      │  │
│    │     "word": "སྐད",              ← Which syllable        │  │
│    │     "position": 8,               ← Character index in text │
│    │     "error_type": "invalid_prefix", ← What's wrong      │  │
│    │     "severity": "error"          ← How bad             │  │
│    │   }                                                      │  │
│    │ ]                                                        │  │
│    └─────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. ERROR POSITION MAPPING (Task 14 - Future)                    │
│    ┌─────────────────────────────────────────────────────────┐  │
│    │ Match text position → PDF position                       │  │
│    │                                                          │  │
│    │ Error at character 8 → "སྐད"                            │  │
│    │ Find "སྐད" in bounding_boxes                            │  │
│    │ → {x: 205, y: 200, w: 48, h: 20, page: 1}               │  │
│    │                                                          │  │
│    │ Result:                                                  │  │
│    │ {                                                        │  │
│    │   "word": "སྐད",                                         │  │
│    │   "error_type": "invalid_prefix",                        │  │
│    │   "page": 1,                                             │  │
│    │   "bbox": {"x": 205, "y": 200, "w": 48, "h": 20}        │  │
│    │ }                                                        │  │
│    └─────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. PDF ANNOTATION (Task 14)                                     │
│    ┌─────────────────────────────────────────────────────────┐  │
│    │ Use ReportLab/PyPDF2 to draw on original PDF:           │  │
│    │                                                          │  │
│    │ For each error:                                          │  │
│    │   - Draw RED UNDERLINE at (x, y+h, w)                   │  │
│    │   - Or RED RECTANGLE around (x, y, w, h)                │  │
│    │   - Add annotation with error_type as tooltip           │  │
│    │                                                          │  │
│    │ Severity-based styling:                                  │  │
│    │   - Critical: Thick red, solid                          │  │
│    │   - Error: Medium red, wavy                             │  │
│    │   - Info: Blue, dotted                                  │  │
│    └─────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. SAVE ANNOTATED PDF                                           │
│    - Save to: /app/results/{job_id}_annotated.pdf              │
│    - Store path in database: jobs.result_path                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. USER DOWNLOADS RESULT                                        │
│    GET /api/v1/spellcheck/result/{job_id}                       │
│    → Returns annotated PDF with errors marked                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Current State (Tasks 4-6): Text-Level Error Detection

### What the Engine Returns Right Now

```python
# Input
text = "བོད་ཀྱི་སྐད་ཡིག་"

# Output from engine.check_text(text)
errors = [
    {
        "word": "སྐད",              # The problematic syllable
        "position": 8,               # Character index in the string
        "error_type": "invalid_prefix",
        "severity": "error"
    }
]
```

### Position Tracking (Current Implementation)

```python
# How we track positions:

text = "བོད་ཀྱི་སྐད་ཡིག་"
#       ^   ^   ^   ^
#       0   4   8   12  ← Character positions

syllables_with_position = [
    {"syllable": "བོད", "position": 0},
    {"syllable": "ཀྱི", "position": 4},
    {"syllable": "སྐད", "position": 8},   ← Error here
    {"syllable": "ཡིག", "position": 12}
]
```

**Key Point**: We track **character positions in the extracted text**, NOT PDF coordinates yet.

---

## Future State (Tasks 13-14): PDF-Level Error Annotation

### The Gap We Need to Bridge

```python
# CURRENT (Text-based):
{
    "word": "སྐད",
    "position": 8,        # Character index in string
    "error_type": "invalid_prefix"
}

# NEEDED (PDF-based):
{
    "word": "སྐད",
    "page": 1,
    "bbox": {
        "x": 205,         # PDF coordinates
        "y": 200,
        "width": 48,
        "height": 20
    },
    "error_type": "invalid_prefix"
}
```

### How We'll Bridge the Gap (Task 13-14)

**Step 1**: Extract text WITH position data from PDF

```python
# OCR returns:
{
    "text": "བོད་ཀྱི་སྐད་ཡིག་",
    "words": [
        {
            "text": "བོད",
            "char_index": 0,      # Maps to our engine position
            "bbox": {"x": 100, "y": 200, "w": 50, "h": 20},
            "page": 1
        },
        {
            "text": "སྐད",
            "char_index": 8,      # Matches error position!
            "bbox": {"x": 205, "y": 200, "w": 48, "h": 20},
            "page": 1
        }
    ]
}
```

**Step 2**: Match error positions to bounding boxes

```python
def map_errors_to_pdf(errors, ocr_data):
    """Map text positions to PDF coordinates"""
    annotated_errors = []
    
    for error in errors:
        # Find word at this character position
        for word_info in ocr_data["words"]:
            if word_info["char_index"] == error["position"]:
                annotated_errors.append({
                    **error,
                    "page": word_info["page"],
                    "bbox": word_info["bbox"]
                })
                break
    
    return annotated_errors
```

**Step 3**: Draw annotations on PDF

```python
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter

def annotate_pdf(original_pdf, errors, output_pdf):
    """Draw error indicators on PDF"""
    reader = PdfReader(original_pdf)
    writer = PdfWriter()
    
    for page_num, page in enumerate(reader.pages):
        # Get errors for this page
        page_errors = [e for e in errors if e["page"] == page_num]
        
        # Create overlay with annotations
        overlay = create_annotation_overlay(page_errors)
        
        # Merge overlay with original page
        page.merge_page(overlay)
        writer.add_page(page)
    
    # Save annotated PDF
    with open(output_pdf, "wb") as f:
        writer.write(f)
```

---

## Data Flow Summary

### Phase 1: Text Extraction (Task 12-13)
```
PDF → OCR/Parser → {
    text: string,
    words: [{text, position, bbox, page}]
}
```

### Phase 2: Spell Check (Tasks 4-6 - Current)
```
text → Spell Checker → [
    {word, position, error_type, severity}
]
```

### Phase 3: Position Mapping (Task 14)
```
errors + word_positions → [
    {word, error_type, page, bbox}
]
```

### Phase 4: PDF Annotation (Task 14)
```
annotated_errors + original_pdf → annotated_pdf
```

---

## Database Storage

```sql
-- Job tracking
CREATE TABLE jobs (
    id UUID PRIMARY KEY,
    file_path TEXT,           -- /app/uploads/{job_id}/original.pdf
    result_path TEXT,         -- /app/results/{job_id}_annotated.pdf
    error_count INTEGER,      -- Total errors found
    status VARCHAR(50),       -- 'completed'
    ...
);

-- Individual errors
CREATE TABLE spell_errors (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES jobs(id),
    word TEXT,                -- "སྐད"
    position INTEGER,         -- Character position in extracted text
    page_number INTEGER,      -- Which PDF page (1-indexed)
    error_type VARCHAR(50),   -- "invalid_prefix"
    severity VARCHAR(20),     -- "error"
    ...
);
```

---

## Why This Architecture?

### Separation of Concerns

1. **Text-level checking** (Tasks 4-6):
   - Pure text processing
   - Fast, testable
   - No PDF dependencies
   - Can test with simple strings

2. **PDF-level annotation** (Tasks 13-14):
   - Separate from spell checking
   - Handles OCR complexity
   - Handles PDF rendering
   - Can swap OCR engines easily

### Benefits

✅ **Testability**: Spell checker tests don't need PDFs  
✅ **Flexibility**: Can check plain text OR PDFs  
✅ **Modularity**: Swap OCR engines without changing spell checker  
✅ **Performance**: Text checking is fast; PDF operations are slow (separate concerns)  
✅ **Interview value**: Shows architectural thinking (separation of concerns)

---

## Current Focus (Tasks 4-6)

Right now we're building:
```python
class TibetanSpellChecker:
    def check_text(self, text: str) -> List[Dict]:
        """
        Input: Plain Tibetan text
        Output: List of errors with character positions
        """
        pass
```

Later (Tasks 13-14) we'll build:
```python
class PDFProcessor:
    def extract_text_with_positions(self, pdf_path: str) -> Dict:
        """Extract text + bounding boxes"""
        pass
    
    def annotate_pdf(self, pdf_path: str, errors: List[Dict]) -> str:
        """Draw error markers on PDF"""
        pass
```

---

## Interview Talking Points

> "I separated the spell checking engine from PDF processing. The engine works on pure text with character-level positions, making it fast and testable without PDF dependencies. For PDF annotation, we'll extract text with bounding box coordinates from OCR, map character positions to PDF coordinates, then use ReportLab to draw error indicators. This separation of concerns means we can test the spell checker independently, swap OCR engines easily, and even use the engine for non-PDF text checking."

Shows:
- Architectural thinking
- Separation of concerns
- Testability focus
- Future flexibility

---

## Questions?

1. **Should error positions be character-based or word-based?**
   - Currently: character index in string
   - Alternative: word index (1st word, 2nd word, etc.)

2. **How should we handle multi-page PDFs?**
   - Process all pages at once
   - Or page-by-page with separate results?

3. **What annotation style do you prefer?**
   - Underline (like MS Word)
   - Rectangle/box (like PDF comments)
   - Highlight background
   - Margin notes

4. **Should we show error details in the PDF?**
   - Tooltip on hover
   - Margin notes
   - Separate error report page

Let me know what you think of this architecture!
