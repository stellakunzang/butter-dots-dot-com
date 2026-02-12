# Simple Architecture Overview

For beginners: This document explains what's happening when you run `docker compose up`.

## The Three Services

When you start the app, Docker creates three separate "containers" (think of them as mini-computers):

```
┌─────────────────────────────────────────────────────────────┐
│                                                               │
│  YOUR BROWSER (http://localhost:3000)                        │
│                                                               │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND (Next.js/React)                                    │
│  - Shows the website                                         │
│  - Handles what users see and click                          │
│  - Runs on port 3000                                         │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            ↓ (makes API calls)
┌─────────────────────────────────────────────────────────────┐
│  BACKEND (Python/FastAPI)                                    │
│  - Handles spell checking logic                              │
│  - Processes PDFs                                            │
│  - Talks to the database                                     │
│  - Runs on port 8000                                         │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            ↓ (reads/writes data)
┌─────────────────────────────────────────────────────────────┐
│  DATABASE (PostgreSQL)                                       │
│  - Stores spell check jobs                                   │
│  - Stores error reports                                      │
│  - Stores dictionary words                                   │
│  - Runs on port 5432                                         │
└─────────────────────────────────────────────────────────────┘
```

## How It Works: A Simple Example

**User uploads a PDF to check spelling:**

1. **Frontend** (http://localhost:3000):
   - User clicks "Upload PDF" button
   - Frontend sends file to backend

2. **Backend** (http://localhost:8000):
   - Receives PDF file
   - Extracts Tibetan text from PDF
   - Checks each word against spelling rules
   - Saves results to database
   - Creates new PDF with errors marked

3. **Database** (PostgreSQL):
   - Stores job information
   - Stores list of errors found
   - Stores valid Tibetan words for checking

4. **Frontend** again:
   - Shows user the list of errors
   - Provides download link for corrected PDF

## File Storage

Files (uploaded PDFs and results) are stored on your computer in:
- `uploads/` - User uploaded files
- `results/` - Generated files with errors marked

These folders are shared between your computer and Docker.

## What Docker Does

Docker:
1. **Creates isolated environments** for each service
2. **Connects them together** so they can talk to each other
3. **Manages starting/stopping** all three services
4. **Handles networking** (ports 3000, 8000, 5432)
5. **Persists data** even when you stop the app

## Development Workflow

When you edit code:

1. **Edit a file** in `frontend/` or `backend/`
2. **Save the file**
3. **Docker notices** the change automatically
4. **Reloads the service** (backend or frontend)
5. **Refresh browser** to see changes

No need to restart Docker!

## Port Reference

| Service | Port | What it does |
|---------|------|--------------|
| Frontend | 3000 | Website users visit |
| Backend API | 8000 | API endpoints |
| API Docs | 8000/docs | Interactive API documentation |
| PostgreSQL | 5432 | Database (internal, not for browsing) |

## Common Commands

**Start everything:**
```bash
docker compose up
```

**Stop everything:**
```bash
docker compose down
```

**See what's running:**
```bash
docker compose ps
```

**See logs:**
```bash
docker compose logs -f backend
```

**Reset database:**
```bash
docker compose down -v
docker compose up
```

## Where to Find Things

| What | Where |
|------|-------|
| Website code | `frontend/` |
| API code | `backend/` |
| Database schema | `database/schema.sql` |
| Configuration | `docker-compose.yml` |
| Documentation | `docs/` |

## Next Steps

Once you have the app running:
1. Browse the frontend at http://localhost:3000
2. Check the API docs at http://localhost:8000/docs
3. Try the "Language Tools" link in the header
4. Start building the spell checker! (see `docs/adr/SPELLCHECKER_DECISIONS.md`)

For detailed technical documentation, see `docs/guides/ARCHITECTURE.md`.
