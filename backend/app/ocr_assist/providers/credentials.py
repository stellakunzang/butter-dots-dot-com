"""Resolve LLM API keys from explicit args, process env, or backend/.env via Settings."""
from __future__ import annotations

import os


def resolve_anthropic_api_key(explicit: str | None = None) -> str | None:
    if explicit:
        return explicit
    env_key = os.environ.get("ANTHROPIC_API_KEY")
    if env_key:
        return env_key
    from app.config import settings

    return settings.anthropic_api_key


def resolve_gemini_api_key(explicit: str | None = None) -> str | None:
    if explicit:
        return explicit
    for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        env_key = os.environ.get(name)
        if env_key:
            return env_key
    from app.config import settings

    return settings.gemini_api_key
