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

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

    @property
    def cors_origins(self) -> list[str]:
        """Parse comma-separated origins into a list."""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
