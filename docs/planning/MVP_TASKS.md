# MVP Task Breakdown - Sequential Order

**Focus**: Complete tasks in order, each builds on previous  
**Interview**: In 2 days

---

## Task Sequence

### **Block 1: Project Foundation**

#### Task 1: Project Setup
- [ ] Create monorepo structure (`frontend/`, `backend/`, `database/`)
- [ ] Create `backend/requirements.txt` with core dependencies
- [ ] Create `backend/Dockerfile`
- [ ] Create `frontend/Dockerfile`
- [ ] Create `docker-compose.yml`
- [ ] Update `.gitignore` for both Python and Node
- [ ] Test: `docker-compose up` starts all services

#### Task 2: Database Schema
- [ ] Create `database/schema.sql` (core tables: jobs, spell_errors, spelling_reference)
- [ ] Create SQLAlchemy models
- [ ] Create database initialization script
- [ ] Test: Tables created correctly
- [ ] Test: Can insert/query records

---

### **Block 2: Core Spell Check Engine**

#### Task 3: Review Existing Script
- [ ] Review user's existing spelling rules script
- [ ] Document what rules it covers
- [ ] Extract reusable logic
- [ ] Identify gaps to fill

#### Task 4: Tibetan Text Utilities
- [ ] Create `backend/app/spellcheck/normalizer.py`
  - Unicode normalization (NFC)
  - Syllable splitting (split on tsheg ་)
  - Character validation (is valid Tibetan Unicode?)
- [ ] Write tests for normalizer
- [ ] Test: Handles various Unicode representations
- [ ] Test: Splits syllables correctly

#### Task 5: Spelling Rules Implementation
- [ ] Create `backend/app/spellcheck/rules.py`
  - Define prefix rules data structure
  - Define suffix rules data structure
  - Define stacking rules data structure
  - Implement validation functions
- [ ] Create test cases (valid syllables, invalid syllables)
- [ ] Test: Rules correctly validate/reject syllables

#### Task 6: Spell Check Engine
- [ ] Create `backend/app/spellcheck/engine.py`
  - Main `TibetanSpellChecker` class
  - Method: `check_text(text) -> List[Error]`
  - Method: `check_syllable(syllable) -> Optional[Error]`
  - Error object with: position, word, error_type, severity
- [ ] Write comprehensive tests
- [ ] Test: Can process full Tibetan text
- [ ] Test: Returns correct errors

**Checkpoint**: Spell check engine works, has tests

---

### **Block 3: API Layer**

#### Task 7: FastAPI Application Setup
- [ ] Create `backend/app/main.py`
- [ ] Configure FastAPI with CORS
- [ ] Add health check endpoint: `GET /health`
- [ ] Create Pydantic schemas (requests/responses)
- [ ] Test: API starts at http://localhost:8000
- [ ] Test: Swagger docs at http://localhost:8000/docs

#### Task 8: Text Spell Check API
- [ ] Create `POST /api/v1/spellcheck/text`
  - Accept: `{"text": "བོད་ཡིག"}`
  - Process with spell check engine
  - Return: `{"errors": [...]}`
- [ ] Test with curl or Postman
- [ ] Test: Various Tibetan texts

#### Task 9: Job Management System
- [ ] Create database CRUD operations for jobs
- [ ] Create `POST /api/v1/spellcheck/job` (create job)
- [ ] Create `GET /api/v1/spellcheck/job/{job_id}` (get status)
- [ ] Implement background task processing with FastAPI BackgroundTasks
- [ ] Test: Can create job, query status
- [ ] Test: Background task executes

**Checkpoint**: API functional, can check text, manage jobs

---

### **Block 4: Basic Frontend Integration**

#### Task 10: Text Spell Checker UI
- [ ] Create `frontend/pages/spellcheck.tsx`
- [ ] Create `frontend/components/spellcheck/TextInput.tsx`
  - Textarea for Tibetan text
  - Submit button
  - Loading state
- [ ] Create `frontend/components/spellcheck/ErrorDisplay.tsx`
  - List of errors
  - Show: word, error type, position
- [ ] Connect to backend API
- [ ] Test: Can paste text, see errors

#### Task 11: Navigation Update
- [ ] Add "Spell Checker" link to Layout
- [ ] Update navigation styling
- [ ] Test: Can navigate to spell checker page

**Checkpoint**: Working text-based spell checker with UI

---

### **Block 5: PDF Processing**

#### Task 12: OCR Integration
- [ ] Create `backend/app/pdf/ocr.py`
- [ ] Integrate Tesseract (pytesseract)
- [ ] Extract text from image-based PDF pages
- [ ] Handle multi-page PDFs
- [ ] Test with sample PDF

#### Task 13: PDF Text Extraction
- [ ] Create `backend/app/pdf/extractor.py`
- [ ] Extract text page by page
- [ ] Preserve position information (bounding boxes)
- [ ] Handle both text-based and image-based PDFs
- [ ] Test: Extract from various PDF types

#### Task 14: PDF Annotation
- [ ] Create `backend/app/pdf/annotator.py`
- [ ] Draw red underlines/circles on errors
- [ ] Add annotations with error details
- [ ] Generate new annotated PDF
- [ ] Test: Annotated PDF displays correctly

**Checkpoint**: Can process PDFs end-to-end

---

### **Block 6: Full Integration**

#### Task 15: PDF Upload API
- [ ] Create `POST /api/v1/spellcheck/upload`
  - Handle multipart file upload
  - Create job record
  - Queue background processing
  - Return job_id
- [ ] Test: Can upload PDF

#### Task 16: Result Download API
- [ ] Create `GET /api/v1/spellcheck/result/{job_id}`
  - Stream annotated PDF file
  - Proper Content-Type headers
  - Handle not found errors
- [ ] Test: Can download result

#### Task 17: Frontend Upload UI
- [ ] Create `frontend/components/spellcheck/FileUpload.tsx`
  - Drag-and-drop file upload
  - File validation (PDF only, size limits)
  - Upload progress
- [ ] Create `frontend/components/spellcheck/JobStatus.tsx`
  - Poll job status
  - Show progress
  - Display when complete
- [ ] Create result download flow
- [ ] Test: Complete upload → process → download flow

**Checkpoint**: Full PDF spell checker working

---

### **Block 7: Polish & Documentation**

#### Task 18: Error Handling
- [ ] Add error messages throughout backend
- [ ] Add error messages throughout frontend
- [ ] Handle edge cases (empty file, corrupt PDF, etc.)
- [ ] Add loading states
- [ ] Test: Graceful failures

#### Task 19: Documentation
- [ ] Update main README with setup instructions
- [ ] Document API endpoints
- [ ] Create `DEMO_SCRIPT.md` for interview walkthrough
- [ ] Add code comments to complex sections

#### Task 20: Final Testing & Validation
- [ ] Test complete flow with multiple PDFs
- [ ] Verify all tests pass
- [ ] Check code quality
- [ ] Practice demo walkthrough
- [ ] List known limitations

**Checkpoint**: Interview-ready demonstration

---

## 🎯 Minimum Viable Checkpoints

**These checkpoints represent working demos:**

### Checkpoint A (Essential):
- Tasks 1-11
- **Demo**: Text-based spell checker
- **Shows**: Core engine, API design, React integration

### Checkpoint B (Target):
- Tasks 1-17
- **Demo**: Full PDF spell checker
- **Shows**: Everything + PDF processing + async jobs

### Checkpoint C (Polish):
- Tasks 1-20
- **Demo**: Production-ready
- **Shows**: Error handling, documentation

---

## 📋 Prerequisites

**Before Task 1:**
- [ ] Docker installed and running
- [ ] Review user's existing spelling rules script
- [ ] Sample Tibetan PDFs available

---

## Next Action

**Share your spelling rules script** so we can proceed with Task 3.

Where is the script, or would you like to paste its contents?
