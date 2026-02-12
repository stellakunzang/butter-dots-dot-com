# Project Structure - Monorepo Setup

**Structure**: Monorepo with separate frontend/backend directories  
**Development**: Docker Compose (Postgres + Python + Next.js)  
**Deployment**: Separate (Frontend: Vercel, Backend: Railway/Heroku)

---

## Directory Structure

```
butter-dots-dot-com/                    (monorepo root)
│
├── frontend/                           (Next.js application)
│   ├── components/                     (React components)
│   │   ├── homepage/
│   │   │   └── DictionaryEntry.tsx
│   │   ├── spellcheck/                 (NEW)
│   │   │   ├── UploadForm.tsx
│   │   │   ├── JobStatus.tsx
│   │   │   ├── ResultsView.tsx
│   │   │   └── ErrorList.tsx
│   │   ├── Layout.tsx
│   │   ├── Button.tsx
│   │   ├── Section.tsx
│   │   └── index.ts
│   ├── pages/
│   │   ├── index.tsx                   (home/dictionary entry)
│   │   ├── resources.tsx               (Tibetan language resources)
│   │   ├── spellcheck.tsx              (NEW - spell checker UI)
│   │   └── api/                        (Next.js API routes - proxy to backend)
│   ├── styles/
│   │   ├── globals.css
│   │   └── *.module.css
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   └── Dockerfile                      (NEW)
│
├── backend/                            (Python FastAPI application)
│   ├── app/
│   │   ├── main.py                     (FastAPI app entry point)
│   │   ├── config.py                   (Settings, environment vars)
│   │   ├── database.py                 (SQLAlchemy setup)
│   │   ├── models/                     (Database models)
│   │   │   ├── __init__.py
│   │   │   ├── job.py
│   │   │   ├── spelling_reference.py
│   │   │   └── user.py
│   │   ├── schemas/                    (Pydantic schemas)
│   │   │   ├── __init__.py
│   │   │   ├── job.py
│   │   │   └── spellcheck.py
│   │   ├── api/                        (API routes)
│   │   │   ├── __init__.py
│   │   │   ├── spellcheck.py
│   │   │   └── health.py
│   │   ├── spellcheck/                 (Core spell check logic)
│   │   │   ├── __init__.py
│   │   │   ├── engine.py               (Main spell checker)
│   │   │   ├── syllable_parser.py     (Parse syllables)
│   │   │   ├── rules.py                (Tibetan grammar rules)
│   │   │   ├── corpus.py               (Dictionary lookup)
│   │   │   └── normalizer.py          (Unicode normalization)
│   │   ├── pdf/                        (PDF processing)
│   │   │   ├── __init__.py
│   │   │   ├── ocr.py                  (Tesseract integration)
│   │   │   ├── extractor.py            (Text extraction)
│   │   │   └── annotator.py            (Mark errors in PDF)
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── email.py                (Email notifications)
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_engine.py
│   │   ├── test_syllable_parser.py
│   │   └── test_rules.py
│   ├── scripts/
│   │   ├── build_corpus.py             (Extract & cross-reference words)
│   │   ├── init_db.py                  (Initialize database)
│   │   └── seed_data.py                (Load corpus)
│   ├── requirements.txt
│   ├── pyproject.toml                  (Optional - Poetry)
│   ├── pytest.ini
│   └── Dockerfile                      (NEW)
│
├── docs/                               (Documentation)
│   ├── SPELLCHECKER_DECISIONS.md      (Architecture Decision Records)
│   ├── MVP_SCOPE.md                    (MVP scope definition)
│   ├── EDUCATIONAL_CONTENT_PLAN.md     (Future educational features)
│   └── PROJECT_STRUCTURE.md            (This file)
│
├── database/                           (Database migrations & seeds)
│   ├── migrations/                     (Alembic migrations)
│   └── schema.sql                      (Initial schema)
│
├── docker-compose.yml                  (Run everything locally)
├── .gitignore
├── README.md                           (Setup instructions)
└── ARCHITECTURE.md                     (Existing architecture doc)
```

---

## Docker Setup (Recommended)

### Why Docker for This Project:

1. **Postgres Setup is Trivial**
   - No manual installation/configuration
   - Starts/stops with everything else
   - Consistent across machines

2. **Python Environment Isolated**
   - No venv confusion
   - Tesseract included in container
   - All dependencies specified

3. **One Command to Rule Them All**
   ```bash
   docker-compose up
   # Postgres + Python + Next.js all running
   ```

4. **Interview Value**
   - Shows DevOps awareness
   - Modern development practices
   - "Containerized for reproducibility"

### docker-compose.yml

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: tibetan_db
    environment:
      POSTGRES_DB: tibetan_spellcheck
      POSTGRES_USER: tibetan
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U tibetan"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Python Backend (FastAPI)
  backend:
    build: ./backend
    container_name: tibetan_backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://tibetan:dev_password@postgres:5432/tibetan_spellcheck
      PYTHONUNBUFFERED: 1
      DEBUG: "true"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./backend:/app
      - ./uploads:/app/uploads  # Shared file storage
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Next.js Frontend
  frontend:
    build: ./frontend
    container_name: tibetan_frontend
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules  # Don't override node_modules
      - /app/.next         # Don't override .next
    depends_on:
      - backend
    command: yarn dev

volumes:
  postgres_data:
```

### Backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

# Install system dependencies (including Tesseract for OCR)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-bod \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Command will be overridden by docker-compose
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json yarn.lock ./

# Install dependencies
RUN yarn install --frozen-lockfile

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Command will be overridden by docker-compose
CMD ["yarn", "dev"]
```

---

## Alternative: No Docker (If You Really Don't Want It)

**Setup would be:**

```bash
# 1. Install Postgres (macOS)
brew install postgresql@15
brew services start postgresql@15
createdb tibetan_spellcheck

# 2. Install Python dependencies
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Install Tesseract
brew install tesseract
brew install tesseract-lang  # For Tibetan support

# 4. Install Node dependencies
cd ../frontend
yarn install

# 5. Start everything (3 terminals)
# Terminal 1: Make sure Postgres is running
brew services start postgresql@15

# Terminal 2: Start backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 3: Start frontend
cd frontend
yarn dev
```

**Downsides:**
- More manual setup
- Different setup on different machines
- Harder to troubleshoot ("works on my machine")
- Need to remember to start Postgres

**Upsides:**
- No Docker learning curve
- Faster edit-refresh cycle (no container overhead)
- Easier to debug (everything visible)

---

## Deployment Strategy

### Development (Local)
```bash
docker-compose up
# Or without Docker: manual setup
```

### Production (Separate Deployments)

**Frontend (Next.js):**
- **Vercel** (Recommended)
  - Push to GitHub
  - Connect repo to Vercel
  - Auto-deploys on push
  - Free tier generous
  - CDN built-in
  
  ```bash
  # Or deploy manually
  cd frontend
  vercel
  ```

**Backend (Python):**
- **Railway.app** (Recommended for MVP)
  - Free tier: 500 hours/month
  - Postgres included
  - Easy setup
  - GitHub integration
  
- **Fly.io** (Alternative)
  - Free tier generous
  - Easy Postgres setup
  
- **Heroku** (Traditional)
  - Easy but not free anymore

**Database:**
- Included with backend hosting (Railway/Fly)
- Or separate: Supabase/Render Postgres (free tiers)

### Environment Variables

**Frontend (.env.local):**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
# In production: https://api.yourdomain.com
```

**Backend (.env):**
```
DATABASE_URL=postgresql://user:pass@localhost:5432/tibetan_spellcheck
DEBUG=true
SECRET_KEY=dev_secret_key_change_in_prod
TESSERACT_PATH=/usr/bin/tesseract
```

---

## Development Workflow

### Day-to-Day Development

**With Docker:**
```bash
# Start everything
docker-compose up

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart a service after changes
docker-compose restart backend

# Stop everything
docker-compose down

# Rebuild after dependency changes
docker-compose up --build
```

**Without Docker:**
```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
yarn dev

# Terminal 3: Database migrations, scripts, etc.
cd backend
source venv/bin/activate
python scripts/build_corpus.py
```

### Database Migrations

```bash
# With Docker
docker-compose exec backend alembic revision --autogenerate -m "Create tables"
docker-compose exec backend alembic upgrade head

# Without Docker
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "Create tables"
alembic upgrade head
```

### Running Tests

```bash
# With Docker
docker-compose exec backend pytest

# Without Docker
cd backend
source venv/bin/activate
pytest
```

---

## Git Strategy

**.gitignore additions:**
```
# Python
backend/venv/
backend/__pycache__/
backend/.pytest_cache/
backend/*.pyc

# Next.js
frontend/.next/
frontend/out/
frontend/node_modules/

# Environment
.env
.env.local
.env.*.local

# Docker
postgres_data/

# Uploads (don't commit user PDFs)
uploads/
results/

# IDE
.vscode/
.idea/
*.swp
```

**Commit Structure:**
```
docs: Add architecture decision records
feat(backend): Implement syllable parser
feat(frontend): Add upload component
fix(backend): Unicode normalization edge case
chore: Set up Docker Compose
```

---

## Interview Demo Strategy

**Option 1: Local Docker Demo (Recommended)**
- ✅ Start with `docker-compose up`
- ✅ Show it running on your laptop
- ✅ Walk through code
- ✅ Explain architecture

**Option 2: Deployed Demo**
- ✅ Live URL to show
- ✅ More impressive
- ❌ More setup time
- ❌ Costs if free tier exceeded

**Option 3: Hybrid**
- Deploy frontend only (Vercel - free)
- Run backend locally during demo
- Show how they connect

---

## Recommendation: Use Docker

**For this project, Docker makes sense because:**

1. ✅ **Learning value** - Senior engineer skill
2. ✅ **Postgres setup** - Trivial with Docker
3. ✅ **Reproducible** - Works same for you and interviewer
4. ✅ **Simple** - Just 3-4 commands you need to know
5. ✅ **Interview talking point** - "Containerized for consistency"

**I'll provide:**
- Complete docker-compose.yml with comments
- Simple Dockerfiles
- Troubleshooting guide
- All commands you need

**You'll learn Docker gradually** while building something useful!

---

## Next Steps

1. ✅ Decide: Docker or no Docker?
2. Create directory structure
3. Set up backend skeleton
4. Set up frontend skeleton
5. Start building!

**My recommendation**: Try Docker. If you hit blockers, we can switch to manual setup. But I think you'll find it easier than expected!

What do you think?
