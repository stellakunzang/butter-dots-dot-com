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

    # OCR model selection. Options: Uchen (default), Woodblock, Ume, Dunhuang.
    # Uchen is best for modern printed texts; Woodblock for traditional block prints.
    # Requires models to be downloaded first: python scripts/download_models.py
    ocr_model_name: str = "Uchen"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

    @property
    def cors_origins(self) -> list[str]:
        """Parse comma-separated origins into a list."""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
