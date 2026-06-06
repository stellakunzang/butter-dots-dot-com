"""
Per-page OCR runner for the interactive OCR workflow.

Wires together the BDRC OCR pipeline, the Phase-1 spellchecker, the Sanskrit
detector, the page quality scorer, and the filesystem job store. See
``docs/planning/INTERACTIVE_OCR_PLAN.md`` § T-05 for the design.

T-05 landed the control flow with no retry loop; T-06 plugs in the Claude
diagnostician and enables the per-page retry loop (up to
``max_attempts``, default 3). T-07 will add the vision-OCR fallback. The
OCR and spellcheck dependencies are injectable so tests (and future
callers) can run without loading the BDRC models or constructing a real
``TibetanSpellChecker``.

Resume is implicit: ``run_all_pages`` skips pages that already have
``final.txt`` on disk, so re-running a job picks up where it left off.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal, Protocol

from app.ocr_assist.diagnostician import (
    AccurateAsSanskrit,
    NeedsHuman,
    RetryWithSettings,
    Verdict as DiagnosticianVerdict,
    verdict_to_dict,
)
from app.ocr_assist.job_store import (
    Job,
    PageState,
    finalize_page,
    load_page,
    save_attempt_verdict,
    save_page_attempt,
    update_page_settings,
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

# Hard cap on OCR attempts per page when the diagnostician is wired in,
# matching the plan's default. Bounds API cost in the absence of a separate
# per-job budget (a future ticket).
DEFAULT_MAX_ATTEMPTS = 3


# The runner's coarse outcome for a page. ``error`` is reserved for pages that
# blew up before a quality verdict could be computed (e.g. the OCR engine was
# unavailable); see ``run_all_pages``.
Decision = Literal["accept", "needs_review", "error"]

# The raw three-way verdict from ``quality.decide``. ``needs_review`` collapses
# both ``escalate`` and ``reject``; carrying the raw verdict lets a caller
# distinguish "borderline, worth another look" from "too damaged to retry".
Verdict = Literal["accept", "escalate", "reject"]


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

    ``decision`` is the runner's coarse verdict for this page: ``"accept"``
    means the page was finalized, ``"needs_review"`` means it's waiting for a
    human (no ``final.txt`` written), and ``"error"`` means the page failed
    before it could be scored (only produced by ``run_all_pages``, which keeps
    going past a failing page — ``run_page`` itself still raises). Inspecting
    the job store for pages where ``final_text is None`` and ``attempts`` is
    non-empty gives the review queue.

    ``verdict`` carries the *raw* ``decide()`` result (``accept`` /
    ``escalate`` / ``reject``) so a caller building a human-review queue can
    tell "borderline, worth another look" (``escalate``) from "too damaged to
    retry" (``reject``) — a distinction ``decision`` deliberately collapses. It
    is ``None`` when ``decision == "error"`` (no quality was computed).

    ``error`` holds the stringified exception when ``decision == "error"`` and
    is ``None`` otherwise.
    """
    page: PageState
    decision: Decision
    quality: PageQuality | None
    verdict: Verdict | None = None
    error: str | None = None


def run_page(
    job: Job,
    page_index: int,
    *,
    thresholds: Thresholds = DEFAULT_THRESHOLDS,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    claude_diagnostician: Any = None,
    ocr: OcrAdapter | None = None,
    spellcheck: SpellcheckAdapter | None = None,
) -> RunResult:
    """Run OCR for one page; retry under the diagnostician's direction.

    With ``claude_diagnostician=None`` the runner does one OCR attempt and
    either accepts the page or queues it for review (no retries).

    With a diagnostician callable, the runner loops up to ``max_attempts``:
    each attempt OCRs with the page's current settings, scores, persists
    the attempt, and either finalizes (``accept``), surfaces for review
    (``needs_human`` verdict from Claude), or applies the verdict's setting
    overrides and retries (``retry_with_settings``). The
    ``accurate_as_sanskrit_accept`` verdict finalizes the current OCR text
    even though structural rules flagged it — that's the whole point of
    the verdict.

    Setting overrides are merged into the page's ``settings.json`` so a
    re-run of this page is deterministic. The page's settings start from
    a copy of the job baseline (see ``job_store.create_job``); retries
    mutate the copy, never the baseline (per the plan's per-page-settings
    rule).
    """
    ocr_fn = ocr or _default_ocr_adapter()
    spellcheck_fn = spellcheck or _default_spellcheck_adapter()

    if claude_diagnostician is None:
        # No retry loop without a diagnostician: one attempt, accept or queue.
        return _run_single_attempt(
            job, page_index, thresholds, ocr_fn, spellcheck_fn
        )

    last_attempt: _AttemptResult | None = None
    for attempt_index in range(max_attempts):
        page = load_page(job, page_index)
        last_attempt = _attempt_once(
            job, page_index, page, ocr_fn, spellcheck_fn, thresholds
        )

        if last_attempt.verdict == "accept":
            updated = finalize_page(
                job,
                page_index,
                final_text=last_attempt.ocr_text,
                final_quality=_quality_to_dict(last_attempt.quality),
            )
            return RunResult(
                page=updated,
                decision="accept",
                quality=last_attempt.quality,
                verdict=last_attempt.verdict,
            )

        # No retries remaining → don't burn an API call we can't act on.
        if attempt_index == max_attempts - 1:
            break

        verdict = claude_diagnostician(
            image_path=page.image_path,
            ocr_text=last_attempt.ocr_text,
            quality=last_attempt.quality,
            prior_attempts=load_page(job, page_index).attempts[:-1],
        )
        _annotate_attempt_verdict(job, page_index, verdict)

        if isinstance(verdict, AccurateAsSanskrit):
            updated = finalize_page(
                job,
                page_index,
                final_text=last_attempt.ocr_text,
                final_quality=_quality_to_dict(last_attempt.quality),
                notes=f"accepted as Sanskrit: {verdict.rationale}",
            )
            return RunResult(
                page=updated,
                decision="accept",
                quality=last_attempt.quality,
                verdict=last_attempt.verdict,
            )
        if isinstance(verdict, NeedsHuman):
            return RunResult(
                page=load_page(job, page_index),
                decision="needs_review",
                quality=last_attempt.quality,
                verdict=last_attempt.verdict,
            )
        if isinstance(verdict, RetryWithSettings):
            _apply_settings_overrides(job, page_index, verdict.settings_overrides)
            continue
        # Defensive — diagnostician contract is a closed union.
        raise TypeError(f"Unknown verdict type: {type(verdict).__name__}")

    # Attempts exhausted without an accept.
    assert last_attempt is not None
    return RunResult(
        page=load_page(job, page_index),
        decision="needs_review",
        quality=last_attempt.quality,
        verdict=last_attempt.verdict,
    )


@dataclass(frozen=True)
class _AttemptResult:
    ocr_text: str
    quality: PageQuality
    verdict: Verdict


def _run_single_attempt(
    job: Job,
    page_index: int,
    thresholds: Thresholds,
    ocr_fn: OcrAdapter,
    spellcheck_fn: SpellcheckAdapter,
) -> RunResult:
    page = load_page(job, page_index)
    attempt = _attempt_once(job, page_index, page, ocr_fn, spellcheck_fn, thresholds)
    if attempt.verdict == "accept":
        updated = finalize_page(
            job,
            page_index,
            final_text=attempt.ocr_text,
            final_quality=_quality_to_dict(attempt.quality),
        )
        return RunResult(
            page=updated,
            decision="accept",
            quality=attempt.quality,
            verdict=attempt.verdict,
        )
    return RunResult(
        page=load_page(job, page_index),
        decision="needs_review",
        quality=attempt.quality,
        verdict=attempt.verdict,
    )


def _attempt_once(
    job: Job,
    page_index: int,
    page: PageState,
    ocr_fn: OcrAdapter,
    spellcheck_fn: SpellcheckAdapter,
    thresholds: Thresholds,
) -> _AttemptResult:
    result = ocr_fn(page.image_path, page.settings)
    spellcheck_errors = spellcheck_fn(result.text)
    quality = score_page(
        result.text,
        spellcheck_errors,
        # line_count is plumbed through but currently inert: with no
        # expected_line_count baseline, quality._line_count_sanity returns 1.0,
        # so the W_LINE_SANITY term contributes nothing to the composite. The
        # signal becomes live once a per-page baseline exists; wiring it now
        # means no signature churn when that lands.
        OcrDiagnostics(line_count=result.line_count),
    )
    save_page_attempt(
        job,
        page_index,
        ocr_text=result.text,
        quality=_quality_to_dict(quality),
    )
    return _AttemptResult(
        ocr_text=result.text, quality=quality, verdict=decide(quality, thresholds)
    )


def _annotate_attempt_verdict(
    job: Job, page_index: int, verdict: DiagnosticianVerdict
) -> None:
    """Attach the diagnostician's verdict to the most recent attempt directory.

    ``save_page_attempt`` already wrote the OCR + quality for this attempt;
    the verdict comes back from Claude after scoring, so we land it in the
    same numbered folder via ``save_attempt_verdict``.
    """
    save_attempt_verdict(job, page_index, verdict_to_dict(verdict))


def _apply_settings_overrides(
    job: Job, page_index: int, overrides: dict[str, Any]
) -> None:
    page = load_page(job, page_index)
    merged = {**page.settings, **overrides}
    update_page_settings(job, page_index, merged)


def run_all_pages(
    job: Job,
    *,
    thresholds: Thresholds = DEFAULT_THRESHOLDS,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    claude_diagnostician: Any = None,
    ocr: OcrAdapter | None = None,
    spellcheck: SpellcheckAdapter | None = None,
) -> list[RunResult]:
    """Run every page in the job; skip pages already finalized on disk.

    A page that raises (e.g. the OCR engine is unavailable or one image is
    unreadable) is recorded as a ``decision="error"`` ``RunResult`` and the run
    continues; one bad page no longer abandons the rest of the batch, and the
    pages that already finalized stay persisted. ``run_page`` itself still
    raises — only the batch surface swallows-and-records.
    """
    ocr_fn = ocr or _default_ocr_adapter()
    spellcheck_fn = spellcheck or _default_spellcheck_adapter()

    results: list[RunResult] = []
    for index in range(1, job.page_count + 1):
        existing = load_page(job, index)
        if existing.final_text is not None:
            # Resume: page was finalized in a prior run, leave it alone.
            logger.info("page %d already finalized; skipping", index)
            continue
        try:
            results.append(
                run_page(
                    job,
                    index,
                    thresholds=thresholds,
                    max_attempts=max_attempts,
                    claude_diagnostician=claude_diagnostician,
                    ocr=ocr_fn,
                    spellcheck=spellcheck_fn,
                )
            )
        except Exception as exc:  # noqa: BLE001 — one bad page must not sink the batch
            logger.exception("page %d failed; recording as error and continuing", index)
            results.append(
                RunResult(
                    page=load_page(job, index),
                    decision="error",
                    quality=None,
                    error=str(exc),
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
