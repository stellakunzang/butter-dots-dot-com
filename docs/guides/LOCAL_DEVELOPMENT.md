# Local development

Docker Desktop is the usual way to run the site. The commands below are the
manual path and the fixes for common setup failures.

## Docker

Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
On Linux: `curl -fsSL https://get.docker.com | sh` and re-login so your user
is in the `docker` group.

```bash
docker compose up               # start everything
docker compose up -d            # start in background
docker compose down             # stop everything
docker compose up --build       # rebuild after dependency changes
docker compose logs -f backend  # one service
```

OCR models are a one-time download, about 300 MB, into gitignored
`backend/OCRModels/` and `backend/Models/`:

```bash
cd backend && python3 scripts/download_models.py
```

## Without Docker

Node.js 20, Python 3.11, PostgreSQL 15, and Yarn.

```bash
brew services start postgresql@15
createdb tibetan_spellcheck
psql tibetan_spellcheck < database/schema.sql

cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install 'setuptools<70' wheel
pip install --no-build-isolation pyewts==0.2.0
pip install -r requirements-dev.txt
python3 scripts/download_models.py
uvicorn app.main:app --reload
```

`pyewts` still imports `pkg_resources`, which setuptools 70 removed. The
pinned setuptools and `--no-build-isolation` are what let that package build.

In another terminal:

```bash
cd frontend && yarn install && yarn dev
```

## Tests

```bash
cd backend && venv/bin/pytest -m "not slow"
cd frontend && yarn test:ci
cd frontend && yarn lint && yarn tsc --noEmit
```

`pytest` with no marker skips the Tashi Gyedpa parity cases when the OCR
models are missing, and `-m "not slow"` skips them even when the models are
present. Run `pytest tests/test_ocr_parity.py` on purpose when changing OCR
or PDF extraction.

## Troubleshooting

**`docker: command not found` or the daemon is not connected.** Docker Desktop
is not running.

**Port 3000, 8000, or 5432 is already allocated.** Stop the other process,
then `docker compose down && docker compose up`. Playwright uses port 3100
so it does not attach to whatever is already on 3000.

**`python: command not found`.** Use `python3`.

**A code change is not showing.** Frontend and backend reload on their own.
`docker compose restart backend` if they do not.

**Reset the database.** `docker compose down -v` removes the volume. The next
`docker compose up` starts empty.
