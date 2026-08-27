"""
OCR diagnostician — backward-compatible re-exports.

Implementation lives in ``app.ocr_assist.providers.anthropic_diagnostician``.
Shared verdict types and the runner contract live in ``app.ocr_assist.contracts``.
"""
from app.ocr_assist.contracts import (
    AccurateAsSanskrit,
    DiagnosticianVerdict,
    NeedsHuman,
    RetryWithSettings,
    Verdict,
    verdict_to_dict,
)
from app.ocr_assist.providers.anthropic_diagnostician import (
    AnthropicDiagnostician,
    DiagnosticianError,
)

# Historical alias used across tests and call sites.
Diagnostician = AnthropicDiagnostician

__all__ = [
    "AccurateAsSanskrit",
    "AnthropicDiagnostician",
    "Diagnostician",
    "DiagnosticianError",
    "DiagnosticianVerdict",
    "NeedsHuman",
    "RetryWithSettings",
    "Verdict",
    "verdict_to_dict",
]
