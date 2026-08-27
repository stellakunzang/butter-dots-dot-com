"""
On-demand Claude vs Gemini vision compare for a single page.

Used by the local QA UI/API after BDRC has already run. Does **not** run during
``run_all_pages`` — each provider call is explicit and per-page.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

from app.ocr_assist.contracts import VisionTranscript, transcript_to_dict
from app.ocr_assist.job_store import Job, load_page, save_vision_transcript
from app.ocr_assist.providers import build_vision_transcriber
from app.ocr_assist.quality import (
    OcrDiagnostics,
    PageQuality,
    ScoringContext,
    Thresholds,
    decide,
    score_page,
)
from app.ocr_assist.runner import DEFAULT_THRESHOLDS, SpellcheckAdapter

logger = logging.getLogger(__name__)

DEFAULT_COMPARE_PROVIDERS: tuple[str, ...] = ("anthropic", "gemini")


@dataclass
class ProviderVisionResult:
    """One provider's compare outcome (success or captured error)."""

    provider: str
    transcript: dict[str, Any] | None = None
    quality: dict[str, Any] | None = None
    composite_score: float | None = None
    decision: str | None = None
    error: str | None = None


@dataclass
class VisionCompareResult:
    page_index: int
    results: list[ProviderVisionResult] = field(default_factory=list)

    def by_provider(self) -> dict[str, ProviderVisionResult]:
        return {r.provider: r for r in self.results}


def compare_vision_providers(
    job: Job,
    page_index: int,
    *,
    providers: Sequence[str] = DEFAULT_COMPARE_PROVIDERS,
    thresholds: Thresholds = DEFAULT_THRESHOLDS,
    spellcheck: SpellcheckAdapter | None = None,
    scoring_context: ScoringContext | None = None,
    transcriber_factory: Callable[[str], Any] | None = None,
) -> VisionCompareResult:
    """Run each vision provider on the page image; persist and return scores.

    Failures for one provider (missing key, missing package, API error) are
    recorded on that provider's result and do not abort the others.
    """
    page = load_page(job, page_index)
    if not page.image_path.is_file():
        raise FileNotFoundError(f"No page image: {page.image_path}")

    spellcheck_fn = spellcheck or _default_spellcheck()
    ctx = scoring_context or ScoringContext(
        expect_mixed_script=bool(job.baseline_settings.get("expect_mixed_script", False))
    )
    factory = transcriber_factory or build_vision_transcriber

    out = VisionCompareResult(page_index=page_index)
    for raw_name in providers:
        provider = raw_name.strip().lower()
        try:
            transcriber = factory(provider)
            transcript: VisionTranscript = transcriber(image_path=page.image_path)
            spellcheck_errors = spellcheck_fn(transcript.text)
            line_count = len(transcript.text.splitlines()) if transcript.text else 0
            diagnostics = OcrDiagnostics(line_count=line_count, expected_line_count=None)
            quality = score_page(transcript.text, spellcheck_errors, diagnostics)
            quality_dict = _quality_to_dict(quality, line_count=line_count)
            decision = decide(quality, thresholds, context=ctx, ocr_diagnostics=diagnostics)
            save_vision_transcript(
                job,
                page_index,
                transcript=transcript_to_dict(transcript),
                quality=quality_dict,
                provider=provider,
            )
            out.results.append(
                ProviderVisionResult(
                    provider=provider,
                    transcript=transcript_to_dict(transcript),
                    quality=quality_dict,
                    composite_score=quality.composite_score,
                    decision=decision,
                )
            )
        except Exception as exc:  # noqa: BLE001 — one provider must not sink the compare
            logger.exception("vision compare failed for provider %s", provider)
            out.results.append(
                ProviderVisionResult(provider=provider, error=str(exc))
            )
    return out


def _default_spellcheck() -> SpellcheckAdapter:
    from app.ocr_assist.runner import _default_spellcheck_adapter

    return _default_spellcheck_adapter()


def _quality_to_dict(quality: PageQuality, *, line_count: int | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "non_tibetan_char_ratio": quality.non_tibetan_char_ratio,
        "structural_error_ratio": quality.structural_error_ratio,
        "sanskrit_adjusted_error_ratio": quality.sanskrit_adjusted_error_ratio,
        "line_count_sanity": quality.line_count_sanity,
        "encoding_error_count": quality.encoding_error_count,
        "unknown_word_ratio": quality.unknown_word_ratio,
        "composite_score": quality.composite_score,
        "breakdown": dict(quality.breakdown),
        "tibetan_only_composite_score": quality.tibetan_only_composite_score,
        "tibetan_syllable_count": quality.tibetan_syllable_count,
        "latin_letter_count": quality.latin_letter_count,
        "repetition_run_length": quality.repetition_run_length,
        "repetition_char": quality.repetition_char,
    }
    if line_count is not None:
        payload["line_count"] = line_count
    return payload
