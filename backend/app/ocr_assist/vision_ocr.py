"""
Vision OCR fallback — backward-compatible re-exports.

Implementations live under ``app.ocr_assist.providers`` (Anthropic and Gemini).
Shared types live in ``app.ocr_assist.contracts``.
"""
from app.ocr_assist.contracts import VisionTranscript, transcript_to_dict
from app.ocr_assist.providers.anthropic_vision import (
    AnthropicVisionTranscriber,
    VisionTranscriberError,
)

# Historical aliases used across tests and call sites.
VisionOcr = AnthropicVisionTranscriber
VisionOcrError = VisionTranscriberError

__all__ = [
    "AnthropicVisionTranscriber",
    "VisionOcr",
    "VisionOcrError",
    "VisionTranscript",
    "VisionTranscriberError",
    "transcript_to_dict",
]
