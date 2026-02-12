# MVP Scope - Tibetan Spell Checker

**Goal**: Interview-ready demonstration by end of week  
**Focus**: Core functionality, clean architecture, defensible decisions

---

## ✅ IN SCOPE (MVP - Phase 1 & 2)

### Core Spell Checking Engine

**Phase 1: Syllable-Level Validation**
- ✓ Validate Tibetan syllable structure
- ✓ Check prefix-base consonant rules
- ✓ Check superscript/subscript stacking rules
- ✓ Check suffix and post-suffix rules
- ✓ Detect impossible letter sequences
- ✓ Unicode normalization (NFC)

**Phase 2: Word-Level Checking**
- ✓ Dictionary lookup against corpus
- ✓ Flag words not in spelling reference
- ✓ Basic frequency-based ranking

### Data & Storage

**Word Corpus:**
- ✓ Multi-source extraction (THDL, Monlam, Rangjung Yeshe)
- ✓ Cross-referencing (require 2+ sources)
- ✓ Confidence scoring
- ✓ 30,000-50,000 validated words (target)

**Database:**
- ✓ PostgreSQL with normalized schema
- ✓ Job tracking (async processing)
- ✓ Error storage (queryable positions)
- ✓ Spelling reference with source tracking
- ✓ User table (email only)

### PDF Processing

**File Handling:**
- ✓ Upload PDF (up to 100MB)
- ✓ Extract text via OCR (Tesseract or Google Vision)
- ✓ Process page by page
- ✓ Annotate PDF with error markers
- ✓ Return downloadable result

**Async Processing:**
- ✓ Background job processing (FastAPI BackgroundTasks)
- ✓ Job status polling
- ✓ Email notification when complete

### API Layer

**Endpoints:**
```
POST /api/v1/spellcheck/upload     → Upload PDF, get job_id
GET  /api/v1/spellcheck/job/:id    → Check job status
GET  /api/v1/spellcheck/result/:id → Download result PDF
POST /api/v1/spellcheck/text       → Quick text check (testing)
```

**Features:**
- ✓ RESTful design
- ✓ Proper status codes (202, 404, etc.)
- ✓ OpenAPI auto-docs (FastAPI)
- ✓ Error handling
- ✓ Type safety (Pydantic models)

### Frontend UI

**Pages:**
- ✓ Upload interface
- ✓ Progress/status display
- ✓ Result download
- ✓ Basic error display

**Components:**
- ✓ File upload with drag-drop
- ✓ Status polling
- ✓ Error list view
- ✓ Download button

### Documentation

**Technical:**
- ✓ Architecture Decision Records (ADRs)
- ✓ API documentation (auto-generated)
- ✓ README with setup instructions
- ✓ Database schema documentation

**User-Facing:**
- ✓ How to use the spell checker
- ✓ Known limitations
- ✓ Wylie display for errors

---

## 📋 DEFERRED (Phase 3+)

### Advanced Features
- ❌ Pronunciation/phonetic transliteration
- ❌ Dialect-specific support (Amdo, Kham, etc.)
- ❌ Multiple transliteration systems (Wylie, THL, phonetic)
- ❌ Sanskrit validation
- ❌ User-submitted word corpus
- ❌ Community moderation
- ❌ Word definitions
- ❌ Etymology information
- ❌ Context-aware suggestions
- ❌ Grammar checking (beyond spelling)
- ❌ Style suggestions

### Complex Infrastructure
- ❌ Celery task queue (using FastAPI BackgroundTasks instead)
- ❌ Redis for caching
- ❌ S3 file storage (using local filesystem)
- ❌ CDN for results
- ❌ Horizontal scaling

### User Features
- ❌ User accounts/authentication
- ❌ User dashboard
- ❌ History of past checks
- ❌ Contribution tracking
- ❌ Gamification/badges

### Educational Content
- ❌ Interactive Unicode visualizations
- ❌ Syllable breakdown tools
- ❌ Dialect comparison pages
- ❌ Wylie vs pronunciation explainer

*Note: Educational content is documented and designed, just not implemented in MVP*

---

## 🎯 Success Criteria

### For Interview

**Must Demonstrate:**
1. ✓ Working end-to-end flow (upload → process → download)
2. ✓ Clean Python/TypeScript code
3. ✓ Proper database design
4. ✓ RESTful API with type safety
5. ✓ Async job processing
6. ✓ Error handling
7. ✓ Tests for core logic
8. ✓ Clear documentation

**Can Discuss:**
1. ✓ Architecture decisions (REST vs GraphQL, etc.)
2. ✓ Trade-offs made (syllable vs word checking)
3. ✓ Scaling plans (Celery, caching, etc.)
4. ✓ Data quality approach (multi-source)
5. ✓ Unicode/Tibetan challenges
6. ✓ Phased roadmap (what's next)
7. ✓ Edge cases identified (Sanskrit, dialects)

**Nice to Have:**
- Deployed demo (vs local only)
- Real OCR working
- Large corpus loaded
- Multiple test documents processed

---

## 📊 Technical Stack (Finalized)

### Backend
- **Language**: Python 3.10+
- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **PDF**: PyPDF2 / reportlab
- **OCR**: Tesseract (pytesseract)
- **Async**: FastAPI BackgroundTasks
- **Testing**: pytest

### Frontend
- **Framework**: Next.js 14
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **HTTP**: fetch / axios
- **State**: React hooks

### Infrastructure
- **Local Dev**: Docker Compose (Postgres, Python, Next.js)
- **Deployment**: TBD (local demo acceptable)

---

## 🗓️ Development Timeline

**Total**: ~4-5 days to interview

### Day 1: Core Engine (8 hours)
- ✓ Set up Python project structure
- ✓ Implement Tibetan text normalization
- ✓ Build syllable parser
- ✓ Implement spelling rules (prefix, suffix, stacking)
- ✓ Write unit tests
- ✓ Deliverable: Spell check engine with tests

### Day 2: Data & Database (8 hours)
- ✓ Research & extract word lists
- ✓ Build cross-referencing script
- ✓ Set up PostgreSQL + schema
- ✓ Populate spelling reference
- ✓ Add word lookup to spell checker
- ✓ Deliverable: Working spell checker with corpus

### Day 3: API & Processing (8 hours)
- ✓ Build FastAPI endpoints
- ✓ Implement file upload handling
- ✓ Add OCR integration
- ✓ Build PDF annotation
- ✓ Add background job processing
- ✓ Deliverable: Working API

### Day 4: Frontend (8 hours)
- ✓ Build upload UI
- ✓ Add status polling
- ✓ Display results
- ✓ Error list view
- ✓ Integrate with API
- ✓ Deliverable: Full user flow

### Day 5: Polish & Prep (4-8 hours)
- ✓ Error handling edge cases
- ✓ Documentation
- ✓ Deploy or prepare demo
- ✓ Practice interview walkthrough
- ✓ Deliverable: Interview-ready

---

## 🚫 Explicitly Out of Scope

### Will NOT Build:
- Real-time collaboration
- Mobile app
- Browser extension
- Desktop app
- Text editor integration
- Translation features
- Speech-to-text
- Text-to-speech
- Machine learning suggestions
- Contextual grammar
- Multi-user editing
- Version control for documents
- Payment processing
- Marketing site

### Will NOT Worry About:
- Production scaling (millions of users)
- DDoS protection
- Advanced security
- GDPR compliance (beyond basics)
- Internationalization (beyond Tibetan/English)
- Analytics/tracking
- A/B testing
- Performance optimization (beyond basics)

---

## 📝 Open Questions (To Resolve Before Starting)

### High Priority:
1. ❓ **Project structure**: Monorepo or separate repos?
2. ❓ **OCR service**: Tesseract or Google Vision API?
3. ❓ **Development environment**: When do you have access to work on this?
4. ❓ **Interview date**: How many days do we have?

### Medium Priority:
5. ❓ **Deployment**: Local demo or hosted?
6. ❓ **Database**: Use Docker for local Postgres?
7. ❓ **Sample data**: Do you have sample Tibetan PDFs for testing?

### Nice to Know:
8. ❓ **Corpus licensing**: Can we legally use THDL/Monlam data?
9. ❓ **Domain name**: If deployed, what URL?
10. ❓ **GitHub**: Public or private repo?

---

## 🎤 Elevator Pitch (30 seconds)

> "I built a Tibetan spell checker that processes PDFs with OCR, validates text against Tibetan grammar rules and a curated word corpus, and returns annotated PDFs marking errors. 
>
> Key decisions: Python for OCR ecosystem, PostgreSQL for scalable data model, phased approach starting with syllable-level checking before dictionary lookup, and multi-source corpus cross-referencing for data quality.
>
> Architecture supports future enhancements: dialect support, user submissions, and Sanskrit handling, all documented in ADRs."

---

## 🎯 What Makes This Interview-Ready

1. **Full Stack**: Python backend + TypeScript frontend
2. **Real Problem**: Tibetan spell checking is genuinely useful
3. **Domain Complexity**: Unicode, syllabic text, linguistic rules
4. **Thoughtful Design**: Phased approach, documented trade-offs
5. **Production Thinking**: Database design, async processing, error handling
6. **Communication**: Clear ADRs, can explain every decision
7. **Realistic Scope**: MVP vs future phases clearly defined
8. **Edge Cases**: Identified Sanskrit, dialects, etc.

---

## Next Action: Get Approval on Open Questions

Once we finalize the open questions, we can:
1. Set up project structure
2. Initialize database
3. Start coding Day 1 tasks

**Ready to proceed?**
