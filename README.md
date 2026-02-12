# Butter Dots Dot Com

A website that started out as a joke but now houses resources for the Orgyen
Khandroling Sangha

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

See [ARCHITECTURE_SIMPLE.md](./ARCHITECTURE_SIMPLE.md) for a beginner-friendly
overview, or
[docs/guides/PROJECT_STRUCTURE.md](./docs/guides/PROJECT_STRUCTURE.md) for
detailed architecture.

## Getting Started (Complete Setup from Scratch)

This guide assumes you're starting with nothing installed. Follow these steps in
order.

### Step 1: Install Docker Desktop

> **First time using Docker?** Think of Docker like a virtual computer that runs
> your app. Instead of installing Python, Node.js, and PostgreSQL separately on
> your machine, Docker creates an isolated environment with everything
> pre-configured. You just click "start" and it works.

**Why Docker?**

- ✅ Run the entire application (frontend, backend, database) with one command
- ✅ No need to install Node.js, Python, PostgreSQL separately
- ✅ Everyone on the team has the exact same setup
- ✅ Easy to start fresh if something breaks

#### macOS Installation:

1. **Download Docker Desktop**:
   - Visit https://www.docker.com/products/docker-desktop/
   - Click "Download for Mac"
   - Choose the right version:
     - **Apple Silicon (M1/M2/M3)**: Download "Mac with Apple chip"
     - **Intel Mac**: Download "Mac with Intel chip"
2. **Install**:
   - Open the downloaded `.dmg` file
   - Drag Docker to your Applications folder
   - Open Docker from Applications
   - Follow the setup wizard (accept terms, allow permissions)
3. **Verify Docker is running**:
   - You should see a Docker whale icon in your menu bar
   - Open Terminal and run:
     ```bash
     docker --version
     ```
   - Should show something like: `Docker version 24.0.x`

#### Windows Installation:

1. Download from https://www.docker.com/products/docker-desktop/
2. Run the installer
3. Enable WSL 2 if prompted
4. Restart your computer
5. Open Docker Desktop from Start menu
6. Verify with: `docker --version` in PowerShell

#### Linux Installation:

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and back in

# Verify
docker --version
```

### Step 2: Clone and Run the Project

1. **Clone the repository**:

   ```bash
   git clone <your-repo-url>
   cd butter-dots-dot-com
   ```

2. **Start everything with one command**:

   ```bash
   docker compose up
   ```

   **Note**: Use `docker compose` (with a space), not `docker-compose` (with a
   hyphen). Docker Compose V2 is built into Docker Desktop.

3. **Wait for everything to start** (first time takes 2-5 minutes):

   You'll see output like:

   ```
   [+] Running 3/3
   ✔ Container tibetan_db       Started
   ✔ Container tibetan_backend  Started
   ✔ Container tibetan_frontend Started
   ```

4. **Open your browser and verify everything works**:
   - **Frontend** (http://localhost:3000):
     - You should see "Butter Dots Dot Com" header
     - Dictionary-style entry for "butter dots"
     - Navigation link to "Language Tools"
   - **Backend API** (http://localhost:8000):
     - Should show: `{"status":"healthy","service":"tibetan-spellchecker"}`
   - **API Docs** (http://localhost:8000/docs):
     - Interactive Swagger UI
     - See all available API endpoints
     - Can test endpoints directly in browser

5. **What you'll see in the terminal**:

   ```
   tibetan_backend   | INFO:     Application startup complete.
   tibetan_backend   | INFO:     Uvicorn running on http://0.0.0.0:8000
   tibetan_frontend  | ▲ Next.js 14.2.0
   tibetan_frontend  | - Local:        http://localhost:3000
   ```

6. **Stop everything** (when done):
   - Press `Ctrl+C` in the terminal
   - Or run: `docker compose down`

### Troubleshooting

**"docker: command not found"**

- Docker Desktop isn't installed or not running
- Check the menu bar (Mac) or system tray (Windows) for the Docker icon
- Make sure Docker Desktop is open and running

**"Cannot connect to the Docker daemon"**

- Docker Desktop isn't running
- Open Docker Desktop and wait for it to fully start (green icon)

**"port is already allocated"**

- Another service is using ports 3000, 8000, or 5432
- Stop other applications using those ports, or:
  ```bash
  docker compose down
  docker compose up
  ```

**"Error response from daemon: pull access denied"**

- No internet connection, or Docker Hub is down
- Wait a moment and try again

**Changes not showing up**

- For backend changes: Docker watches automatically, no restart needed
- For frontend changes: Docker watches automatically, no restart needed
- If still not working, restart: `docker compose restart backend` or `frontend`

## Quick Reference

**Start the app**:

```bash
docker compose up
```

**Start in background** (daemon mode):

```bash
docker compose up -d
```

**View logs**:

```bash
docker compose logs -f          # All services
docker compose logs -f backend  # Just backend
docker compose logs -f frontend # Just frontend
```

**Stop the app**:

```bash
docker compose down
```

**Rebuild after changing dependencies**:

```bash
docker compose up --build
```

**Access database directly**:

```bash
docker compose exec postgres psql -U tibetan -d tibetan_spellcheck
```

## Alternative: Run Without Docker (Manual Setup)

Start all services (Postgres + Backend + Frontend):

```bash
docker-compose up
```

Access:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

View logs:

```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

Stop everything:

```bash
docker-compose down
```

## Alternative: Run Without Docker (Manual Setup)

If you prefer not to use Docker, you can run each service manually.

### Prerequisites (Without Docker):

- Node.js 20.x (from https://nodejs.org)
- Python 3.11+ (from https://python.org)
- PostgreSQL 15+ (from https://postgresql.org or `brew install postgresql@15`)
- Yarn (`npm install -g yarn`)

### Setup Steps:

**1. Install PostgreSQL and create database**:

```bash
# macOS
brew install postgresql@15
brew services start postgresql@15
createdb tibetan_spellcheck
psql tibetan_spellcheck < database/schema.sql
```

**2. Start Backend** (in one terminal):

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs at http://localhost:8000

**3. Start Frontend** (in another terminal):

```bash
cd frontend
yarn install
yarn dev
```

Frontend runs at http://localhost:3000

**Note**: You'll need 3 terminals open (Postgres, Backend, Frontend) vs Docker's
single command.

## Testing

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
yarn test
```

### Run All Tests (CI Mode)

```bash
cd backend && pytest && cd ../frontend && yarn test:ci
```

GitHub Actions automatically runs all tests on push/PR.

### Building for Production

**Frontend**:

```bash
cd frontend
yarn build
yarn start
```

**Backend**:

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Docker Production Build**:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Architecture

This is a full-stack application with:

- **Frontend**: Next.js, React, TypeScript, Tailwind CSS
- **Backend**: Python, FastAPI, SQLAlchemy
- **Database**: PostgreSQL
- **Testing**: pytest (backend), Jest (frontend)
- **CI/CD**: GitHub Actions

See [docs/guides/ARCHITECTURE.md](./docs/guides/ARCHITECTURE.md) for detailed
architecture documentation.

### Key Principles

- **TDD**: Test-Driven Development with pragmatic coverage
- **Monorepo**: Frontend and backend in one repository
- **Containerization**: Docker Compose for consistent environments
- **Type Safety**: TypeScript (frontend) + Pydantic (backend)
- **Component-Based**: Reusable UI components with Tailwind CSS

### Quick Reference

- **Frontend**: `frontend/` directory (Next.js, React, Tailwind)
- **Backend**: `backend/` directory (FastAPI, SQLAlchemy)
- **Database**: `database/` directory (PostgreSQL schema)
- **Docs**: `docs/` directory (ADRs, guides, planning)
- **Change colors/design**: Edit `frontend/tailwind.config.js`
- **Add API endpoint**: Create in `backend/app/api/`
- **Add page**: Create in `frontend/pages/`, use `Layout` component

## Pages

### Home (`/`)

The main landing page featuring the iconic butter dots image and description.

### Resources (`/resources`)

A comprehensive guide for installing Tibetan fonts and keyboards, including:

- Automated installation script for macOS
- Manual installation instructions for macOS, Windows, and Linux
- Recommended Tibetan fonts (Tibetan Machine Uni, Jomolhari, Monlam Uni, DDC
  Uchen)
- Keyboard installation guides for all major platforms
- Wylie transliteration guide and examples
- Links to additional Tibetan language resources

## Deployment

### Deploying to Vercel (Recommended)

Vercel is the easiest way to deploy Next.js apps and is created by the Next.js
team.

#### Option 1: Deploy via Git Integration (Recommended)

1. Push your code to GitHub, GitLab, or Bitbucket
2. Go to [vercel.com](https://vercel.com/new)
3. Import your repository
4. Vercel will automatically detect Next.js and configure build settings
5. Click "Deploy"

**Automatic deployments**: After initial setup, every push to your main branch
automatically deploys to production, and every pull request gets a preview URL.

#### Option 2: Deploy via Vercel CLI

1. Install Vercel CLI:

```bash
npm i -g vercel
```

2. Run deployment command from your project directory:

```bash
vercel
```

3. Follow the prompts to link your project

4. For production deployment:

```bash
vercel --prod
```

### Deploying Changes

Once set up with git integration:

1. Make your changes locally
2. Test locally with `yarn dev`
3. Commit your changes:

```bash
git add .
git commit -m "Description of your changes"
```

4. Push to your repository:

```bash
git push origin main
```

5. Vercel automatically builds and deploys your changes (usually takes 30-60
   seconds)
6. You'll receive a deployment URL in your Vercel dashboard

### Other Deployment Options

- **Netlify**: Connect your git repository at [netlify.com](https://netlify.com)
- **AWS Amplify**: Use the Amplify Console to deploy from git
- **Self-hosted**: Build with `yarn build` and serve the `.next` folder with
  `yarn start`

## Image Optimization

The butter dots image is optimized for web:

- Resized to 900×1200px (maintains 3:4 aspect ratio)
- Compressed to ~331KB for fast loading
- Uses Next.js Image component for automatic optimization

To optimize new images:

```bash
# Install ImageMagick or use sips (macOS)
sips -Z 1200 --setProperty format jpeg --setProperty formatOptions 80 input.jpg --out output.jpg
```

## Frequently Asked Questions

### Do I need to know Docker to use this?

No! Just install Docker Desktop and run `docker compose up`. That's it. You
don't need to understand how Docker works.

### What if I don't want to use Docker?

See the "Alternative: Run Without Docker" section above. You'll need to install
Node.js, Python, and PostgreSQL manually.

### How do I make changes to the code?

1. Edit files in `frontend/` for website changes
2. Edit files in `backend/` for API changes
3. Docker automatically reloads when you save files
4. Refresh your browser to see changes

### Where is the database stored?

Docker stores it in a volume (isolated from your machine). To reset the
database:

```bash
docker compose down -v  # -v removes volumes
docker compose up       # Fresh database
```

### Can I use this on Windows?

Yes! Install Docker Desktop for Windows and follow the same instructions. Use
PowerShell instead of Terminal.

### How do I stop the app from running in the background?

```bash
docker compose down
```

### The app is slow or using too much memory?

Docker Desktop → Settings → Resources → Increase memory/CPU allocation

### How do I update dependencies?

**Frontend**:

```bash
cd frontend
yarn add package-name
docker compose up --build
```

**Backend**:

```bash
cd backend
# Add to requirements.txt
docker compose up --build
```

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [Docker Getting Started](https://docs.docker.com/get-started/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## Support

For issues or questions:

1. Check the FAQ above
2. Check [SETUP_COMPLETE.md](./SETUP_COMPLETE.md) for verification steps
3. Open an issue in the repository
