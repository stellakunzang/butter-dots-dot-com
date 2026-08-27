"""
Application settings loaded from environment variables / .env file.

Pydantic Settings automatically reads from:
  1. Environment variables (highest priority)
  2. A .env file in the backend/ directory
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # CORS
    allowed_origins: str = "http://localhost:3000"

    # App
    debug: bool = False
    port: int = 8000

    # Public base URL — used in email notifications so users get a working download link.
    # In production set this to your Render/Railway backend URL, e.g. https://api.butterdots.com
    public_base_url: str = "http://localhost:8000"

    # OCR model selection. Available: Woodblock, Woodblock-Stacks, Modern, Ume_Druma, Ume_Petsuk.
    # Woodblock is best for standard printed Uchen script (including Word/digital fonts).
    # Requires models to be downloaded first: python scripts/download_models.py
    ocr_model_name: str = "Woodblock"

    # Database URL for the spelling reference / word corpus.
    # When unset, dictionary lookup is silently skipped and only structural
    # (Phase 1) validation runs.  Set to a postgres:// DSN for full Phase 2 support.
    database_url: str | None = None

    # Interactive OCR assist (local-only; used by app.ocr_assist when --enable-ai).
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None
    diagnostician_provider: str = "anthropic"
    vision_ocr_provider: str = "anthropic"

    # Local QA UI/API for interactive OCR. Off by default — never enable in prod.
    ocr_assist_local: bool = False
    ocr_assist_jobs_root: str = "jobs"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

    @property
    def cors_origins(self) -> list[str]:
        """Parse comma-separated origins into a list."""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
