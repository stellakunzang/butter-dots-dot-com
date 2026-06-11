"""
Per-page OCR runner for the interactive OCR workflow.

Wires together the BDRC OCR pipeline, the Phase-1 spellchecker, the Sanskrit
detector, the page quality scorer, and the filesystem job store. See
``docs/planning/INTERACTIVE_OCR_PLAN.md`` § T-05 for the design.

T-05 landed the control flow with no retry loop; T-06 plugs in the AI
diagnostician and enables the per-page retry loop (up to ``max_attempts``,
default 3); T-07 adds a vision-OCR fallback that runs after retries exhaust
(or the diagnostician returns ``NeedsHuman``), either finalizing the page
from the vision transcript or attaching it to the human-review record. The OCR, spellcheck, diagnostician, and vision
dependencies are all injectable so tests (and future callers) can run
without loading BDRC models, the spellchecker database, or the Anthropic
SDK.

Resume is implicit: ``run_all_pages`` skips pages that already have
``final.txt`` on disk, so re-running a job picks up where it left off.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal, Protocol

from app.ocr_assist.contracts import (
    AccurateAsSanskrit,
    DiagnosticianCallable,
    DiagnosticianVerdict,
    NeedsHuman,
    RetryWithSettings,
    VisionTranscriberCallable,
    VisionTranscript,
    transcript_to_dict,
    verdict_to_dict,
)
from app.ocr_assist.job_store import (
    AttemptRecord,
    Job,
    PageState,
    finalize_page,
    load_page,
    save_attempt_verdict,
    save_page_attempt,
    save_vision_transcript,
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
    diagnostician: DiagnosticianCallable | None = None,
    vision_transcriber: VisionTranscriberCallable | None = None,
    ocr: OcrAdapter | None = None,
    spellcheck: SpellcheckAdapter | None = None,
) -> RunResult:
    """Run OCR for one page; retry under the diagnostician's direction.

    With ``diagnostician=None`` the runner does one OCR attempt and
    either accepts the page or queues it for review (no retries).

    With a diagnostician callable, the runner loops up to ``max_attempts``:
    each attempt OCRs with the page's current settings, scores, persists
    the attempt, and either finalizes (``accept``), surfaces for review
    (``needs_human`` verdict), or applies the verdict's setting overrides
    and retries (``retry_with_settings``). The ``accurate_as_sanskrit_accept``
    verdict finalizes the current OCR text even though structural rules flagged
    it — that's the whole point of the verdict.

    With ``vision_transcriber`` also wired, any path that would otherwise
    return ``needs_review`` (attempts exhausted or ``needs_human`` from the
    diagnostician) first asks a vision model to read the image directly. The
    vision transcript is scored with the same quality scorer; if it clears
    ``accept`` the page finalizes from vision, otherwise the transcript is
    persisted next to the page (``vision_ocr.json`` / ``vision_quality.json``)
    so the human review surface can show both engines' reads. Vision is never
    called on a page that already accepted on a BDRC attempt — the fallback
    only runs when BDRC failed.

    Setting overrides are merged into the page's ``settings.json`` so a
    re-run of this page is deterministic. The page's settings start from
    a copy of the job baseline (see ``job_store.create_job``); retries
    mutate the copy, never the baseline (per the plan's per-page-settings
    rule).
    """
    if max_attempts < 1:
        raise ValueError(f"max_attempts must be >= 1, got {max_attempts}")

    ocr_fn = ocr or _default_ocr_adapter()
    spellcheck_fn = spellcheck or _default_spellcheck_adapter()

    if diagnostician is None:
        # No retry loop without a diagnostician: one attempt, accept or queue.
        # Vision fallback still runs on a needs_review outcome if configured.
        result = _run_single_attempt(
            job, page_index, thresholds, ocr_fn, spellcheck_fn
        )
        if result.decision == "accept" or vision_transcriber is None:
            return result
        return _try_vision_fallback(
            job,
            page_index,
            vision_transcriber,
            spellcheck_fn,
            thresholds,
            bdrc_quality=result.quality,
            bdrc_verdict=result.verdict,
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

        verdict = diagnostician(
            image_path=page.image_path,
            ocr_text=last_attempt.ocr_text,
            quality=last_attempt.quality,
            prior_attempts=load_page(job, page_index).attempts,
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
            # NeedsHuman means the diagnostician judged the *BDRC retry path*
            # unrecoverable; vision is a different engine and may still succeed.
            return _try_vision_fallback(
                job,
                page_index,
                vision_transcriber,
                spellcheck_fn,
                thresholds,
                bdrc_quality=last_attempt.quality,
                bdrc_verdict=last_attempt.verdict,
                needs_human_reason=verdict.reason,
            )
        if isinstance(verdict, RetryWithSettings):
            if not verdict.settings_overrides:
                logger.warning(
                    "diagnostician returned retry_with_settings with empty overrides "
                    "(rationale=%r); skipping redundant OCR",
                    verdict.rationale,
                )
                break
            _apply_settings_overrides(job, page_index, verdict.settings_overrides)
            continue
        # Defensive — diagnostician contract is a closed union.
        raise TypeError(f"Unknown verdict type: {type(verdict).__name__}")

    # Attempts exhausted without an accept.
    assert last_attempt is not None
    return _try_vision_fallback(
        job,
        page_index,
        vision_transcriber,
        spellcheck_fn,
        thresholds,
        bdrc_quality=last_attempt.quality,
        bdrc_verdict=last_attempt.verdict,
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
    the verdict comes back from the diagnostician after scoring, so we land it in the
    same numbered folder via ``save_attempt_verdict``.
    """
    save_attempt_verdict(job, page_index, verdict_to_dict(verdict))


def _apply_settings_overrides(
    job: Job, page_index: int, overrides: dict[str, Any]
) -> None:
    page = load_page(job, page_index)
    merged = {**page.settings, **overrides}
    update_page_settings(job, page_index, merged)


def _try_vision_fallback(
    job: Job,
    page_index: int,
    vision_transcriber: VisionTranscriberCallable | None,
    spellcheck_fn: SpellcheckAdapter,
    thresholds: Thresholds,
    *,
    bdrc_quality: PageQuality,
    bdrc_verdict: Verdict,
    needs_human_reason: str | None = None,
) -> RunResult:
    """Run the vision-OCR fallback and route based on its score.

    Returns a needs_review result built from the BDRC last-attempt signals if
    no vision callable is wired — preserving the pre-T-07 behavior so callers
    that didn't opt in to vision see no change. Otherwise reads the page
    image via ``vision_ocr``, scores the transcript with the same scorer, and
    either finalizes the page from vision or persists the transcript next to
    the page for human review.
    """
    page = load_page(job, page_index)

    if vision_transcriber is None:
        return RunResult(
            page=page,
            decision="needs_review",
            quality=bdrc_quality,
            verdict=bdrc_verdict,
        )

    transcript = vision_transcriber(image_path=page.image_path)
    spellcheck_errors = spellcheck_fn(transcript.text)
    # Vision returns a single transcribed string; ``line_count`` comes from
    # splitting on newlines (the prompt tells the model to preserve line breaks).
    # Without an ``expected_line_count`` baseline the line-sanity signal stays
    # neutral, matching what BDRC attempts get today.
    line_count = len(transcript.text.splitlines()) if transcript.text else 0
    quality = score_page(
        transcript.text,
        spellcheck_errors,
        OcrDiagnostics(line_count=line_count),
    )
    quality_dict = _quality_to_dict(quality)
    save_vision_transcript(
        job,
        page_index,
        transcript=transcript_to_dict(transcript),
        quality=quality_dict,
    )
    verdict = decide(quality, thresholds)

    if verdict == "accept":
        notes = _vision_accept_notes(transcript, needs_human_reason)
        updated = finalize_page(
            job,
            page_index,
            final_text=transcript.text,
            final_quality=quality_dict,
            notes=notes,
        )
        return RunResult(
            page=updated,
            decision="accept",
            quality=quality,
            verdict=verdict,
        )

    # Vision didn't clear accept either — surface to human with both reads on
    # disk. Carry the BDRC quality on the result so the review surface knows
    # which engine is dimmer; the vision_quality is loaded separately from the
    # page state.
    return RunResult(
        page=load_page(job, page_index),
        decision="needs_review",
        quality=bdrc_quality,
        verdict=bdrc_verdict,
    )


def _vision_accept_notes(
    transcript: VisionTranscript, needs_human_reason: str | None
) -> str:
    parts = ["accepted via vision fallback"]
    if transcript.notes:
        parts.append(f"vision notes: {transcript.notes}")
    if needs_human_reason:
        parts.append(f"diagnostician flagged: {needs_human_reason}")
    return "\n".join(parts)


def run_all_pages(
    job: Job,
    *,
    thresholds: Thresholds = DEFAULT_THRESHOLDS,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    diagnostician: DiagnosticianCallable | None = None,
    vision_transcriber: VisionTranscriberCallable | None = None,
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
                    diagnostician=diagnostician,
                    vision_transcriber=vision_transcriber,
                    ocr=ocr_fn,
                    spellcheck=spellcheck_fn,
                )
            )
        except Exception as exc:  # noqa: BLE001 — one bad page must not sink the batch
            logger.exception("page %d failed; recording as error and continuing", index)
            # Reuse the page object loaded at the top of the loop rather than
            # re-`load_page`-ing here: if the failure was *in* ``load_page``
            # itself (corrupt page dir, bad settings.json) it would have raised
            # above, never reaching this branch — but reloading now would hit
            # the same fault and propagate out, defeating the per-page
            # resilience guarantee.
            results.append(
                RunResult(
                    page=existing,
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
    or trigger the model load. Per-page ``settings`` (from ``settings.json``)
    are forwarded into ``BDRCOCREngine.run_on_image`` so diagnostician
    retry overrides actually change OCR behavior.
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

        lines = engine.run_on_image(image, page_settings=settings)
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
