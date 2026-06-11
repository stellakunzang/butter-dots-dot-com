"""
Provider-agnostic types and callables for the interactive OCR AI loop.

The runner depends on these contracts, not on a specific LLM vendor. Concrete
implementations live under ``app.ocr_assist.providers``.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal, Protocol, Union

from app.ocr_assist.job_store import AttemptRecord
from app.ocr_assist.quality import PageQuality


@dataclass(frozen=True)
class VisionTranscript:
    """A vision model's literal read of a page image."""
    text: str
    notes: str | None = None


@dataclass(frozen=True)
class RetryWithSettings:
    settings_overrides: dict[str, Any]
    rationale: str


@dataclass(frozen=True)
class AccurateAsSanskrit:
    rationale: str


@dataclass(frozen=True)
class NeedsHuman:
    reason: str


DiagnosticianVerdict = Union[RetryWithSettings, AccurateAsSanskrit, NeedsHuman]

# Historical alias used in diagnostician tests and docs.
Verdict = DiagnosticianVerdict


class DiagnosticianCallable(Protocol):
    """Retry decision-maker: image + OCR + quality → next action."""

    def __call__(
        self,
        *,
        image_path: Path,
        ocr_text: str,
        quality: PageQuality,
        prior_attempts: list[AttemptRecord],
    ) -> DiagnosticianVerdict: ...


class VisionTranscriberCallable(Protocol):
    """Vision fallback: page image → literal transcript."""

    def __call__(self, *, image_path: Path) -> VisionTranscript: ...


def verdict_to_dict(verdict: DiagnosticianVerdict) -> dict[str, Any]:
    """Serialize a verdict for persistence under ``attempts/NN/ai_verdict.json``."""
    if isinstance(verdict, RetryWithSettings):
        return {
            "tool": "retry_with_settings",
            "settings_overrides": dict(verdict.settings_overrides),
            "rationale": verdict.rationale,
        }
    if isinstance(verdict, AccurateAsSanskrit):
        return {"tool": "accurate_as_sanskrit_accept", "rationale": verdict.rationale}
    if isinstance(verdict, NeedsHuman):
        return {"tool": "needs_human", "reason": verdict.reason}
    raise TypeError(f"Unknown verdict type: {type(verdict).__name__}")


def transcript_to_dict(transcript: VisionTranscript) -> dict[str, Any]:
    """Serialize a transcript for persistence next to the page state."""
    payload: dict[str, Any] = {"text": transcript.text}
    if transcript.notes is not None:
        payload["notes"] = transcript.notes
    return payload


ProviderName = Literal["anthropic", "gemini"]
