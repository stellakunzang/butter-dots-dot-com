from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import corpus, health, spellcheck
from app.config import settings

app = FastAPI(
    title="Tibetan Spellchecker API",
    version="0.1.0",
    description="API for Tibetan spell checking with PDF support"
)

# CORS — origins loaded from ALLOWED_ORIGINS env var / .env file
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(spellcheck.router, prefix="/api/v1", tags=["spellcheck"])
app.include_router(corpus.router, prefix="/api/v1", tags=["corpus"])
