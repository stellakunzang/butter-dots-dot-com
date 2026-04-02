# Butter Dots Dot Com

A website that started out as a joke but now houses Tibetan language resources
for the Orgyen Khandroling Sangha

## Documentation

All project documentation has been organized in the `/docs` directory:

- **`/docs/guides`** - Developer guides (architecture, components, setup)
- **`/docs/adr`** - Architecture Decision Records
- **`/docs/planning`** - Project planning and roadmaps
- **`/docs/research`** - External resources and references
- **`/docs/archive`** - Historical/completed documentation

See [`/docs/README.md`](./docs/README.md) for the complete documentation index.

## Project Structure

This is a monorepo containing:

- **`frontend/`** - Next.js web application
- **`backend/`** - Python FastAPI service
- **`database/`** - PostgreSQL schema and migrations
- **`docs/`** - All project documentation

See [docs/guides/PROJECT_STRUCTURE.md](./docs/guides/PROJECT_STRUCTURE.md) for
detailed architecture.

## Running Locally

Docker Desktop is the only prerequisite — it runs the frontend, backend, and
database together with a single command.

### Install Docker Desktop

- **macOS**:
  [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
  — choose "Mac with Apple chip" (M1/M2/M3) or "Mac with Intel chip"
- **Windows**: Same link → run installer → enable WSL 2 if prompted → restart
- **Linux**:
  `curl -fsSL https://get.docker.com | sh && sudo usermod -aG docker $USER` (log
  out and back in after)

Verify it's running: `docker --version`

### Start the App

1. Clone the repository:

   ```bash
   git clone <your-repo-url>
   cd butter-dots-dot-com
   ```

2. Download the OCR models (one-time setup, ~300 MB):

   ```bash
   cd backend
   python3 scripts/download_models.py
   cd ..
   ```

   Models are saved to `backend/OCRModels/` and `backend/Models/` (gitignored).
   You only need to do this once.

3. Start everything:

   ```bash
   docker compose up
   ```

   First run takes 2–5 minutes to build. You'll know it's ready when you see:

   ```
   tibetan_backend   | INFO:     Application startup complete.
   tibetan_frontend  | - Local:        http://localhost:3000
   ```

4. Open in your browser:
   - **App**: http://localhost:3000
   - **API**: http://localhost:8000
   - **API docs** (Swagger UI): http://localhost:8000/docs

5. To stop: press `Ctrl+C`, or run `docker compose down` from another terminal.

## Quick Reference

```bash
docker compose up               # start everything
docker compose up -d            # start in background
docker compose down             # stop everything
docker compose up --build       # rebuild after changing dependencies
docker compose logs -f          # stream all logs
docker compose logs -f backend  # stream backend logs only
docker compose logs -f frontend # stream frontend logs only
```

## Troubleshooting

**`docker: command not found`** Docker Desktop isn't installed or isn't running.
Check the menu bar (Mac) or system tray (Windows) for the Docker whale icon.

**`Cannot connect to the Docker daemon`** Docker Desktop is installed but not
running. Open it and wait for the green "running" indicator before retrying.

**`port is already allocated`** Something else is using port 3000, 8000,
or 5432. Stop the conflicting process, then:

```bash
docker compose down
docker compose up
```

**`python: command not found` (or similar)** Use `python3` instead of `python` —
macOS and Linux don't include a bare `python` command.

**Changes not showing up** Both frontend and backend have hot reload. If it's
still stale:

```bash
docker compose restart backend   # or: frontend
```

**App is slow or using too much memory** Docker Desktop → Settings → Resources →
increase memory and CPU allocation.

**Reset the database**

```bash
docker compose down -v  # -v removes the database volume
docker compose up
```

**Windows** Use PowerShell instead of Terminal. Everything else is the same.

## Alternative: Run Without Docker

If you prefer to run services manually, you'll need:

- Node.js 20.x — [nodejs.org](https://nodejs.org)
- Python 3.11+ — [python.org](https://python.org)
- PostgreSQL 15+ — `brew install postgresql@15` (macOS) or
  [postgresql.org](https://postgresql.org)
- Yarn — `npm install -g yarn`

**1. Set up the database** (macOS):

```bash
brew services start postgresql@15
createdb tibetan_spellcheck
psql tibetan_spellcheck < database/schema.sql
```

**2. Start the backend** (in one terminal):

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install 'setuptools<70' wheel
pip install --no-build-isolation pyewts==0.2.0
pip install -r requirements.txt
python3 scripts/download_models.py  # one-time
uvicorn app.main:app --reload
```

> **Why the extra pip steps?** The `pyewts` package uses a legacy `setup.py`
> that imports `pkg_resources`, which was removed in `setuptools` 70+. Pinning
> an older `setuptools` and disabling build isolation lets it build correctly.

**3. Start the frontend** (in another terminal):

```bash
cd frontend
yarn install
yarn dev
```

## Testing

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && yarn test

# Both (CI mode)
cd backend && pytest && cd ../frontend && yarn test:ci
```

GitHub Actions runs all tests automatically on push and pull request.

## Architecture

- **Frontend**: Next.js, React, TypeScript, Tailwind CSS
- **Backend**: Python, FastAPI, SQLAlchemy
- **Database**: PostgreSQL
- **OCR**: [BDRC Tibetan OCR](https://github.com/buda-base/tibetan-ocr-app)
  (onnxruntime, MIT licensed)
- **CI/CD**: GitHub Actions → Netlify (frontend) + Render (backend)

Quick navigation:

| What you want to change | Where to look                 |
| ----------------------- | ----------------------------- |
| Page content / UI       | `frontend/pages/`             |
| Reusable components     | `frontend/components/`        |
| Colors / design tokens  | `frontend/tailwind.config.js` |
| API endpoints           | `backend/app/api/`            |
| Database schema         | `database/schema.sql`         |

See [docs/guides/ARCHITECTURE.md](./docs/guides/ARCHITECTURE.md) for more
detail.

## Deployment

The frontend is hosted on **Netlify** and the backend is hosted on **Render**.
Both are connected to this GitHub repository — pushing to `main` triggers an
automatic redeployment of both services. No manual steps needed.

The sections below document the initial setup in case anything needs to be
reconfigured.

### Frontend: Netlify

1. Go to [app.netlify.com](https://app.netlify.com) → **Add new site → Import an
   existing project**
2. Connect your GitHub repository
3. Set the following build settings:
   - **Base directory**: `frontend`
   - **Build command**: `yarn build`
   - **Publish directory**: `frontend/.next`
4. Click **Deploy site**

Netlify installs the Next.js runtime plugin automatically on the first build.

### Backend: Render

1. Go to [render.com](https://render.com) → **New → Web Service**
2. Connect your GitHub repository
3. Set the following:
   - **Root directory**: `backend`
   - **Runtime**: Docker
   - **Branch**: `main`
4. Add these environment variables:

| Variable          | Value                        | Notes                                         |
| ----------------- | ---------------------------- | --------------------------------------------- |
| `ALLOWED_ORIGINS` | `https://butterdots.com`     | Your Netlify frontend URL                     |
| `PUBLIC_BASE_URL` | `https://api.butterdots.com` | Used in email result links                    |
| `OCR_MODEL_NAME`  | `Uchen`                      | OCR model: Uchen, Woodblock, Ume, or Dunhuang |

5. Click **Create Web Service**

The first Docker build takes ~5 minutes because the OCR models (~300 MB) are
downloaded during the build. Subsequent deploys use the cached Docker layer and
are much faster.

## Acknowledgments

The syllable validation rules are based on **Paul G. Hackett's Tibetan
Spell-checker v1.0** (Columbia University, 2011), originally written in VBA for
Microsoft Word and released under GNU GPL v3. The core "exclusive pattern"
approach — defining _invalid_ syllable constructions rather than enumerating all
valid ones — was ported to Python and extended with structured error reporting
and position tracking. See
[`docs/research/SCRIPT_ANALYSIS.md`](docs/research/SCRIPT_ANALYSIS.md) for the
full analysis.

The PDF OCR feature uses the **BDRC Tibetan OCR** engine, developed by
[Eric Werner](https://github.com/buda-base) for the
[Buddhist Digital Resource Center](https://www.bdrc.io/) in partnership with the
[Monlam AI](https://monlam.ai/) team. It is released under the MIT license.

The OCR models were trained on transcriptions from BDRC,
[Asian Legacy Library](https://asianlegacylibrary.org/),
[Adarsha](https://adarshah.org/), and NorbuKetaka, and represent the first
publicly available OCR system with strong support for classical Tibetan scripts
(Uchen, Woodblock, Ume, and Dunhuang).

- GitHub:
  [buda-base/tibetan-ocr-app](https://github.com/buda-base/tibetan-ocr-app)
- Models: [HuggingFace / BDRC](https://huggingface.co/BDRC) and
  [OpenPecha](https://huggingface.co/openpecha)
