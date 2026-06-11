"""LLM provider factories for the interactive OCR AI loop."""
from __future__ import annotations

import os
from typing import Any

from app.ocr_assist.contracts import (
    DiagnosticianCallable,
    VisionTranscriberCallable,
)
from app.ocr_assist.providers.anthropic_diagnostician import AnthropicDiagnostician
from app.ocr_assist.providers.anthropic_vision import AnthropicVisionTranscriber
from app.ocr_assist.providers.gemini_vision import GeminiVisionTranscriber


def build_diagnostician(
    provider: str | None = None,
    **kwargs: Any,
) -> DiagnosticianCallable:
    """Construct a diagnostician for ``provider`` (default: env or anthropic)."""
    name = _normalize_provider(provider or os.environ.get("DIAGNOSTICIAN_PROVIDER", "anthropic"))
    if name == "anthropic":
        return AnthropicDiagnostician(**kwargs)
    raise ValueError(f"Unknown diagnostician provider: {name!r}")


def build_vision_transcriber(
    provider: str | None = None,
    **kwargs: Any,
) -> VisionTranscriberCallable:
    """Construct a vision transcriber for ``provider`` (default: env or anthropic)."""
    name = _normalize_provider(provider or os.environ.get("VISION_OCR_PROVIDER", "anthropic"))
    if name == "anthropic":
        return AnthropicVisionTranscriber(**kwargs)
    if name == "gemini":
        return GeminiVisionTranscriber(**kwargs)
    raise ValueError(f"Unknown vision OCR provider: {name!r}")


def _normalize_provider(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"anthropic", "claude"}:
        return "anthropic"
    if normalized in {"gemini", "google"}:
        return "gemini"
    return normalized
