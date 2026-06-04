"""
Per-page OCR runner for the interactive OCR workflow.

Wires together the BDRC OCR pipeline, the Phase-1 spellchecker, the Sanskrit
detector, the page quality scorer, and the filesystem job store. See
``docs/planning/INTERACTIVE_OCR_PLAN.md`` § T-05 for the design.

This ticket lands the control flow only. With no Claude diagnostician
available, a page is either auto-accepted or queued for human review — no
retries happen. T-06 will plug in the diagnostician and enable the loop;
T-07 will add the vision-OCR fallback. The OCR and spellcheck dependencies
are injectable so tests (and future callers) can run without loading the
BDRC models or constructing a real ``TibetanSpellChecker``.

Resume is implicit: ``run_all_pages`` skips pages that already have
``final.txt`` on disk, so re-running a job picks up where it left off.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal, Protocol

from app.ocr_assist.job_store import (
    Job,
    PageState,
    finalize_page,
    load_page,
    save_page_attempt,
)
from app.ocr_assist.quality import (
    OcrDiagnostics,
    PageQuality,
    Thresholds,
    decide,
    score_page,
)


logger = logging.getLogger(__name__)


# Starting thresholds for the runner. T-10 calibrates these against a real
# target text; until then these mirror the values used in T-03's tests.
DEFAULT_THRESHOLDS = Thresholds(accept=0.85, reject=0.5)


Decision = Literal["accept", "needs_review"]


@dataclass(frozen=True)
class OcrResult:
    """Output of an OCR adapter call: raw text plus the detected line count.

    ``line_count`` feeds the quality scorer's ``OcrDiagnostics``. It is the
    number of lines BDRC actually recognized on the page, not a count of
    newlines in ``text`` (which would conflate joined and split lines).
    """
    text: str
    line_count: int


class OcrAdapter(Protocol):
    """Reads a page image and returns BDRC OCR output.

    The default implementation calls into ``app.pdf.ocr`` and requires the
    ONNX models to be downloaded. Tests inject a fake that returns canned
    text without touching disk-loaded models.
    """
    def __call__(self, image_path: Path, settings: dict[str, Any]) -> OcrResult: ...


SpellcheckAdapter = Callable[[str], list[dict[str, Any]]]


@dataclass(frozen=True)
class RunResult:
    """Outcome of running a single page through the loop.

    ``decision`` is the runner's verdict for this page: ``"accept"`` means
    the page was finalized, ``"needs_review"`` means it's waiting for a
    human (no ``final.txt`` written). Inspecting the job store for pages
    where ``final_text is None`` and ``attempts`` is non-empty gives the
    review queue.
    """
    page: PageState
    decision: Decision
    quality: PageQuality


def run_page(
    job: Job,
    page_index: int,
    *,
    thresholds: Thresholds = DEFAULT_THRESHOLDS,
    claude_diagnostician: Any = None,
    ocr: OcrAdapter | None = None,
    spellcheck: SpellcheckAdapter | None = None,
) -> RunResult:
    """Run OCR + quality scoring for one page; finalize or queue for review.

    With ``claude_diagnostician=None`` (the only mode shipped in T-05) the
    runner does a single OCR attempt and either accepts the page or queues
    it for human review. Retries land in T-06 alongside the Claude call.
    """
    if claude_diagnostician is not None:
        # Keep the surface honest: until T-06 wires the diagnostician in,
        # silently accepting a non-None argument here would let callers
        # believe retries were running when they aren't.
        raise NotImplementedError(
            "claude_diagnostician integration ships in T-06; pass None for now."
        )

    page = load_page(job, page_index)
    ocr_fn = ocr or _default_ocr_adapter()
    spellcheck_fn = spellcheck or _default_spellcheck_adapter()

    result = ocr_fn(page.image_path, page.settings)
    spellcheck_errors = spellcheck_fn(result.text)
    quality = score_page(
        result.text,
        spellcheck_errors,
        OcrDiagnostics(line_count=result.line_count),
    )
    verdict = decide(quality, thresholds)

    save_page_attempt(
        job,
        page_index,
        ocr_text=result.text,
        quality=_quality_to_dict(quality),
    )

    if verdict == "accept":
        updated = finalize_page(
            job,
            page_index,
            final_text=result.text,
            final_quality=_quality_to_dict(quality),
        )
        return RunResult(page=updated, decision="accept", quality=quality)

    # escalate or reject without an AI loop → queue for human review.
    return RunResult(
        page=load_page(job, page_index),
        decision="needs_review",
        quality=quality,
    )


def run_all_pages(
    job: Job,
    *,
    thresholds: Thresholds = DEFAULT_THRESHOLDS,
    claude_diagnostician: Any = None,
    ocr: OcrAdapter | None = None,
    spellcheck: SpellcheckAdapter | None = None,
) -> list[RunResult]:
    """Run every page in the job; skip pages already finalized on disk."""
    ocr_fn = ocr or _default_ocr_adapter()
    spellcheck_fn = spellcheck or _default_spellcheck_adapter()

    results: list[RunResult] = []
    for index in range(1, job.page_count + 1):
        existing = load_page(job, index)
        if existing.final_text is not None:
            # Resume: page was finalized in a prior run, leave it alone.
            logger.info("page %d already finalized; skipping", index)
            continue
        results.append(
            run_page(
                job,
                index,
                thresholds=thresholds,
                claude_diagnostician=claude_diagnostician,
                ocr=ocr_fn,
                spellcheck=spellcheck_fn,
            )
        )
    return results


def _quality_to_dict(quality: PageQuality) -> dict[str, Any]:
    return {
        "non_tibetan_char_ratio": quality.non_tibetan_char_ratio,
        "structural_error_ratio": quality.structural_error_ratio,
        "sanskrit_adjusted_error_ratio": quality.sanskrit_adjusted_error_ratio,
        "line_count_sanity": quality.line_count_sanity,
        "encoding_error_count": quality.encoding_error_count,
        "unknown_word_ratio": quality.unknown_word_ratio,
        "composite_score": quality.composite_score,
        "breakdown": dict(quality.breakdown),
    }


def _default_ocr_adapter() -> OcrAdapter:
    """OCR adapter backed by the BDRC singleton.

    Lazy import so test runs that inject a fake never touch onnxruntime
    or trigger the model load. Settings are persisted in the page dir but
    not yet read here — per-page setting overrides drive OCR variants in
    T-06, when retries actually exercise them.
    """
    def _adapter(image_path: Path, settings: dict[str, Any]) -> OcrResult:
        import cv2
        from app.pdf.ocr import get_engine

        engine = get_engine()
        if not engine.ready:
            raise RuntimeError(f"OCR engine unavailable: {engine.error}")

        image = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
        if image is None:
            raise RuntimeError(f"Failed to read page image at {image_path}")

        lines = engine.run_on_image(image)
        text = "\n".join(line.text for line in lines if line.text)
        return OcrResult(text=text, line_count=len(lines))

    return _adapter


def _default_spellcheck_adapter() -> SpellcheckAdapter:
    """Spellcheck adapter backed by ``TibetanSpellChecker``.

    Constructed lazily on the first call so importing this module doesn't
    open a database connection through ``DictionaryService``.
    """
    checker = None

    def _adapter(text: str) -> list[dict[str, Any]]:
        nonlocal checker
        if checker is None:
            from app.spellcheck.engine import TibetanSpellChecker
            checker = TibetanSpellChecker()
        return checker.check_text(text)

    return _adapter
