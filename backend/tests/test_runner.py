"""
Tests for the per-page OCR runner (T-05 + T-06).

T-05 covers the no-AI path: high-score pages auto-accept, low-score pages
queue for review, ``run_all_pages`` skips finalized pages and survives a
single failing page.

T-06 adds the Claude diagnostician retry loop. The diagnostician is stubbed
with a callable so the suite never makes a real API call. Covers:

- ``RetryWithSettings`` merges overrides into the page's settings.json and
  the next attempt sees them.
- ``AccurateAsSanskrit`` finalizes the current OCR text with the rationale
  in the page notes.
- ``NeedsHuman`` queues for review without finalizing.
- ``max_attempts`` caps the loop; the diagnostician is not consulted on the
  final attempt (the verdict can't be acted on).
- The diagnostician's verdict is persisted into the attempt's ai_verdict.json.

OCR and spellcheck are injected as fakes so the suite never loads BDRC models
or opens a database connection.
"""
import json
from pathlib import Path

import pytest
from PIL import Image

from app.ocr_assist import job_store
from app.ocr_assist.diagnostician import (
    AccurateAsSanskrit,
    NeedsHuman,
    RetryWithSettings,
)
from app.ocr_assist.job_store import (
    create_job,
    load_page,
    save_page_attempt,
    finalize_page,
)
from app.ocr_assist.quality import Thresholds
from app.ocr_assist.runner import (
    DEFAULT_THRESHOLDS,
    OcrResult,
    run_all_pages,
    run_page,
)
from app.ocr_assist.contracts import VisionTranscript


CLEAN_TEXT = "བཀྲ་ཤིས་བདེ་ལེགས།\nདགེ་བའི་བཤེས་གཉེན།"
GARBLED_TEXT = "xxxx hello yyy zzz totally not tibetan at all"


@pytest.fixture
def fake_pdf(monkeypatch):
    """Bypass pdf2image: render to a small list of in-memory PIL images."""
    def _fake_render(pdf_bytes: bytes, *, dpi: int):
        return [Image.new("RGB", (40, 40), "white") for _ in range(3)]

    monkeypatch.setattr(job_store, "_render_pdf", _fake_render)
    return b"fake-pdf-bytes"


@pytest.fixture
def job(tmp_path: Path, fake_pdf):
    return create_job(
        fake_pdf,
        source_file="sample.pdf",
        baseline_settings={"model_variant": "Modern"},
        jobs_root=tmp_path,
    )


def clean_ocr(image_path: Path, settings: dict) -> OcrResult:
    return OcrResult(text=CLEAN_TEXT, line_count=2)


def garbled_ocr(image_path: Path, settings: dict) -> OcrResult:
    return OcrResult(text=GARBLED_TEXT, line_count=1)


def no_errors(text: str) -> list[dict]:
    return []


def class_errors(text: str) -> list[dict]:
    return [
        {"word": "xxx", "error_type": "invalid_subscript_combination", "severity": "critical"},
    ]


class TestRunPageAccept:
    def test_clean_page_finalizes(self, job):
        result = run_page(job, 1, ocr=clean_ocr, spellcheck=no_errors)

        assert result.decision == "accept"
        assert result.page.final_text == CLEAN_TEXT
        assert result.quality.composite_score > 0.95
        assert (job.root / "page-001" / "final.txt").is_file()

    def test_attempt_persisted_for_accepted_page(self, job):
        run_page(job, 1, ocr=clean_ocr, spellcheck=no_errors)
        page = load_page(job, 1)
        assert len(page.attempts) == 1
        assert page.attempts[0].ocr_text == CLEAN_TEXT
        assert page.attempts[0].quality is not None
        assert page.attempts[0].quality["composite_score"] > 0.95


class TestRunPageNeedsReview:
    def test_low_score_page_does_not_finalize(self, job):
        # All-non-Tibetan text pegs non_tibetan_char_ratio at 1.0 → composite=0.75
        # (penalty 0.25), between reject=0.5 and accept=0.85, so decide() escalates.
        result = run_page(job, 1, ocr=garbled_ocr, spellcheck=no_errors)

        assert result.decision == "needs_review"
        assert result.page.final_text is None
        assert not (job.root / "page-001" / "final.txt").is_file()

    def test_needs_review_still_records_attempt(self, job):
        run_page(job, 1, ocr=garbled_ocr, spellcheck=no_errors)
        page = load_page(job, 1)
        assert len(page.attempts) == 1
        assert page.attempts[0].ocr_text == GARBLED_TEXT

    def test_encoding_error_blocks_accept_even_at_high_score(self, job):
        # Clean text + a single encoding_error severity=critical → hard floor
        # in `decide` forces escalate.
        def bad_spellcheck(text: str) -> list[dict]:
            return [{
                "word": "བཀྲ",
                "error_type": "encoding_error",
                "severity": "critical",
            }]

        result = run_page(job, 1, ocr=clean_ocr, spellcheck=bad_spellcheck)
        assert result.decision == "needs_review"
        assert result.page.final_text is None


class TestNoRetries:
    def test_low_score_only_one_attempt(self, job):
        # A bad page produces exactly one OCR attempt: no retry loop runs.
        calls = []

        def counting_ocr(image_path: Path, settings: dict) -> OcrResult:
            calls.append(image_path)
            return OcrResult(text=GARBLED_TEXT, line_count=1)

        run_page(job, 1, ocr=counting_ocr, spellcheck=no_errors)
        assert len(calls) == 1


class TestRunAllPages:
    def test_runs_every_page(self, job):
        results = run_all_pages(job, ocr=clean_ocr, spellcheck=no_errors)
        assert len(results) == job.page_count
        assert all(r.decision == "accept" for r in results)
        for i in range(1, job.page_count + 1):
            assert (job.root / f"page-{i:03d}" / "final.txt").is_file()

    def test_skips_already_finalized_pages(self, job):
        # Pre-finalize page 2 by hand; runner should not OCR it on the next pass.
        finalize_page(
            job,
            2,
            final_text="manually finalized",
            final_quality={"composite_score": 1.0},
        )

        ocr_calls: list[Path] = []

        def counting_ocr(image_path: Path, settings: dict) -> OcrResult:
            ocr_calls.append(image_path)
            return OcrResult(text=CLEAN_TEXT, line_count=2)

        results = run_all_pages(job, ocr=counting_ocr, spellcheck=no_errors)

        # Page 2 was already final → 2 pages OCR'd (pages 1 and 3), not 3.
        assert len(ocr_calls) == 2
        assert {r.page.index for r in results} == {1, 3}
        # Pre-finalized text is preserved.
        assert load_page(job, 2).final_text == "manually finalized"


class TestRawVerdict:
    def test_accept_page_carries_accept_verdict(self, job):
        result = run_page(job, 1, ocr=clean_ocr, spellcheck=no_errors)
        assert result.decision == "accept"
        assert result.verdict == "accept"

    def test_escalate_page_carries_escalate_verdict(self, job):
        # Garbled all-non-Tibetan text scores composite=0.75, between the
        # default reject=0.5 and accept=0.85 → escalate (folded into
        # needs_review). The raw verdict still distinguishes it from reject.
        result = run_page(job, 1, ocr=garbled_ocr, spellcheck=no_errors)
        assert result.decision == "needs_review"
        assert result.verdict == "escalate"

    def test_reject_page_carries_reject_verdict(self, job):
        # Push reject above the garbled page's 0.75 composite so it genuinely
        # rejects rather than escalates — exercising the path that is otherwise
        # indistinguishable from escalate through `decision` alone.
        strict = Thresholds(accept=0.85, reject=0.8)
        result = run_page(
            job, 1, ocr=garbled_ocr, spellcheck=no_errors, thresholds=strict
        )
        assert result.decision == "needs_review"
        assert result.verdict == "reject"


class TestRunAllPagesResilience:
    def test_one_failing_page_does_not_abort_batch(self, job):
        # OCR blows up on page 2 only; pages 1 and 3 must still run and the
        # failure must surface as a decision="error" result rather than an
        # exception that kills the loop.
        def flaky_ocr(image_path: Path, settings: dict) -> OcrResult:
            if image_path.parent.name == "page-002":
                raise RuntimeError("OCR engine unavailable: boom")
            return OcrResult(text=CLEAN_TEXT, line_count=2)

        results = run_all_pages(job, ocr=flaky_ocr, spellcheck=no_errors)

        assert len(results) == job.page_count
        by_index = {r.page.index: r for r in results}
        assert by_index[1].decision == "accept"
        assert by_index[3].decision == "accept"

        failed = by_index[2]
        assert failed.decision == "error"
        assert failed.quality is None
        assert failed.verdict is None
        assert "boom" in failed.error
        # The failed page was never finalized.
        assert failed.page.final_text is None
        assert not (job.root / "page-002" / "final.txt").is_file()

    def test_recovery_does_not_reload_the_failed_page(self, job, monkeypatch):
        # Regression guard: the per-page recovery branch must build its error
        # RunResult from the page object already loaded at the top of the loop,
        # not by re-reading the page. If it reloaded and the underlying fault
        # were *in* load_page (corrupt settings.json), that reload would raise
        # and sink the whole batch. Here a reload of page 2 after its initial
        # load is forced to fail; the batch must still complete.
        from app.ocr_assist import runner as runner_mod

        real_load_page = runner_mod.load_page
        load_counts: dict[int, int] = {}

        def flaky_load_page(job, index):
            load_counts[index] = load_counts.get(index, 0) + 1
            # First load (top of loop) and the load inside the attempt succeed;
            # any *further* reload of page 2 — i.e. a recovery-branch reload —
            # raises, standing in for a corrupt page dir on re-read.
            if index == 2 and load_counts[index] >= 3:
                raise RuntimeError("settings.json corrupt on reload")
            return real_load_page(job, index)

        monkeypatch.setattr(runner_mod, "load_page", flaky_load_page)

        def flaky_ocr(image_path: Path, settings: dict) -> OcrResult:
            if image_path.parent.name == "page-002":
                raise RuntimeError("OCR engine unavailable: boom")
            return OcrResult(text=CLEAN_TEXT, line_count=2)

        results = run_all_pages(job, ocr=flaky_ocr, spellcheck=no_errors)

        assert len(results) == job.page_count
        by_index = {r.page.index: r for r in results}
        assert by_index[1].decision == "accept"
        assert by_index[3].decision == "accept"
        assert by_index[2].decision == "error"
        assert "boom" in by_index[2].error
        # The recovery branch never reloaded page 2 (would have been call #3).
        assert load_counts[2] == 2


class TestMaxAttemptsGuard:
    def test_zero_max_attempts_raises_value_error(self, job):
        # A diagnostician-driven run with max_attempts=0 has no attempt to act
        # on; reject it cleanly rather than tripping an internal assertion.
        diagnostician = _stub_diagnostician([])  # never called
        with pytest.raises(ValueError, match="max_attempts"):
            run_page(
                job,
                1,
                ocr=garbled_ocr,
                spellcheck=no_errors,
                diagnostician=diagnostician,
                max_attempts=0,
            )


class TestThresholdsOverride:
    def test_lax_thresholds_accept_garbled(self, job):
        # The garbled page is rejected under DEFAULT_THRESHOLDS (see
        # TestRunPageNeedsReview); lowering accept to 0 flips it to accept.
        lax = Thresholds(accept=0.0, reject=0.0)
        result = run_page(
            job, 1, ocr=garbled_ocr, spellcheck=no_errors, thresholds=lax
        )
        assert result.decision == "accept"
        assert result.page.final_text == GARBLED_TEXT


class TestDefaultThresholds:
    def test_defaults_match_t03_test_values(self):
        # Sanity guard: T-10 calibrates these — when that ticket lands,
        # the new values should be documented and this test updated.
        assert DEFAULT_THRESHOLDS.accept == 0.85
        assert DEFAULT_THRESHOLDS.reject == 0.5


# ---------------------------------------------------------------------------
# T-06 — diagnostician retry loop
# ---------------------------------------------------------------------------


def _stub_diagnostician(verdicts):
    """Build a diagnostician callable that yields ``verdicts`` in order.

    Each invocation pops the next verdict. Test failures are clearer when the
    stub asserts on exhaustion rather than running off the end silently.
    """
    iterator = iter(verdicts)
    calls: list[dict] = []

    def _fake(*, image_path, ocr_text, quality, prior_attempts):
        calls.append(
            {
                "image_path": image_path,
                "ocr_text": ocr_text,
                "composite": quality.composite_score,
                "prior_attempt_count": len(prior_attempts),
            }
        )
        return next(iterator)

    _fake.calls = calls  # type: ignore[attr-defined]
    return _fake


class TestDiagnosticianRetryWithSettings:
    def test_overrides_merge_into_page_settings(self, job):
        # First attempt OCRs garbled text (below accept); diagnostician asks
        # to retry with k_factor=3.0; second attempt also garbled → exhausts
        # attempts. Settings.json should have the override applied.
        diagnostician = _stub_diagnostician(
            [RetryWithSettings(settings_overrides={"k_factor": 3.0}, rationale="x")]
        )

        run_page(
            job,
            1,
            ocr=garbled_ocr,
            spellcheck=no_errors,
            diagnostician=diagnostician,
            max_attempts=2,
        )

        settings = json.loads(
            (job.root / "page-001" / "settings.json").read_text()
        )
        # Baseline ``model_variant`` is preserved; the override is layered on.
        assert settings["model_variant"] == "Modern"
        assert settings["k_factor"] == 3.0

    def test_second_attempt_sees_new_settings(self, job):
        # The runner should pass the *updated* settings dict to the OCR
        # adapter on the second attempt, not the baseline.
        settings_seen: list[dict] = []

        def recording_ocr(image_path: Path, settings: dict) -> OcrResult:
            settings_seen.append(dict(settings))
            return OcrResult(text=GARBLED_TEXT, line_count=1)

        diagnostician = _stub_diagnostician(
            [RetryWithSettings(settings_overrides={"k_factor": 4.2}, rationale="x")]
        )

        run_page(
            job,
            1,
            ocr=recording_ocr,
            spellcheck=no_errors,
            diagnostician=diagnostician,
            max_attempts=2,
        )

        assert len(settings_seen) == 2
        assert "k_factor" not in settings_seen[0]
        assert settings_seen[1]["k_factor"] == 4.2

    def test_empty_overrides_skip_redundant_ocr(self, job):
        # Empty settings_overrides would rerun identical OCR; skip to vision path.
        settings_seen: list[dict] = []

        def recording_ocr(image_path: Path, settings: dict) -> OcrResult:
            settings_seen.append(dict(settings))
            return OcrResult(text=GARBLED_TEXT, line_count=1)

        diagnostician = _stub_diagnostician(
            [RetryWithSettings(settings_overrides={}, rationale="try again")]
        )

        result = run_page(
            job,
            1,
            ocr=recording_ocr,
            spellcheck=no_errors,
            diagnostician=diagnostician,
            max_attempts=3,
        )

        assert len(settings_seen) == 1
        assert result.decision == "needs_review"


class TestDiagnosticianAccurateAsSanskrit:
    def test_finalizes_current_text_with_notes(self, job):
        diagnostician = _stub_diagnostician(
            [AccurateAsSanskrit(rationale="anusvara-heavy mantra block")]
        )

        result = run_page(
            job,
            1,
            ocr=garbled_ocr,
            spellcheck=no_errors,
            diagnostician=diagnostician,
            max_attempts=3,
        )

        assert result.decision == "accept"
        assert result.page.final_text == GARBLED_TEXT
        assert (job.root / "page-001" / "final.txt").is_file()
        assert result.page.notes is not None
        assert "anusvara-heavy mantra block" in result.page.notes


class TestDiagnosticianNeedsHuman:
    def test_needs_human_queues_for_review(self, job):
        diagnostician = _stub_diagnostician(
            [NeedsHuman(reason="image is upside-down and torn")]
        )

        result = run_page(
            job,
            1,
            ocr=garbled_ocr,
            spellcheck=no_errors,
            diagnostician=diagnostician,
            max_attempts=3,
        )

        assert result.decision == "needs_review"
        assert result.page.final_text is None
        # Verdict was persisted onto the attempt.
        verdict_path = job.root / "page-001" / "attempts" / "01" / "ai_verdict.json"
        verdict = json.loads(verdict_path.read_text())
        assert verdict["tool"] == "needs_human"
        assert "torn" in verdict["reason"]


class TestMaxAttempts:
    def test_loop_stops_at_max_attempts(self, job):
        # All attempts come back garbled; diagnostician keeps asking for retries.
        # The runner must cap the loop at max_attempts and not consult the
        # diagnostician on the last attempt (verdict can't be acted on).
        diagnostician = _stub_diagnostician(
            [
                RetryWithSettings(settings_overrides={"k_factor": 3.0}, rationale="a"),
                RetryWithSettings(settings_overrides={"k_factor": 4.0}, rationale="b"),
                # Third entry deliberately omitted — accessing it would raise
                # StopIteration, which proves the loop didn't call again.
            ]
        )

        ocr_calls: list[Path] = []

        def counting_ocr(image_path: Path, settings: dict) -> OcrResult:
            ocr_calls.append(image_path)
            return OcrResult(text=GARBLED_TEXT, line_count=1)

        result = run_page(
            job,
            1,
            ocr=counting_ocr,
            spellcheck=no_errors,
            diagnostician=diagnostician,
            max_attempts=3,
        )

        assert len(ocr_calls) == 3
        assert len(diagnostician.calls) == 2  # not called on the final attempt
        assert result.decision == "needs_review"
        assert result.page.final_text is None

    def test_no_diagnostician_call_when_first_attempt_accepts(self, job):
        diagnostician = _stub_diagnostician([])  # would explode if called

        result = run_page(
            job,
            1,
            ocr=clean_ocr,
            spellcheck=no_errors,
            diagnostician=diagnostician,
            max_attempts=3,
        )

        assert result.decision == "accept"
        assert diagnostician.calls == []


class TestVerdictPersistence:
    def test_retry_verdict_recorded_on_attempt(self, job):
        diagnostician = _stub_diagnostician(
            [
                RetryWithSettings(
                    settings_overrides={"model_variant": "Woodblock"},
                    rationale="probably a pecha page",
                ),
            ]
        )

        run_page(
            job,
            1,
            ocr=garbled_ocr,
            spellcheck=no_errors,
            diagnostician=diagnostician,
            max_attempts=2,
        )

        # Verdict landed on attempt 1 (the one that triggered the retry).
        verdict_path = job.root / "page-001" / "attempts" / "01" / "ai_verdict.json"
        verdict = json.loads(verdict_path.read_text())
        assert verdict == {
            "tool": "retry_with_settings",
            "settings_overrides": {"model_variant": "Woodblock"},
            "rationale": "probably a pecha page",
        }


# ---------------------------------------------------------------------------
# T-07 — Claude vision-OCR fallback
# ---------------------------------------------------------------------------


def _stub_vision(transcripts):
    """Build a vision-OCR callable that yields ``transcripts`` in order.

    Mirrors ``_stub_diagnostician``: each call pops the next transcript and
    appends to ``.calls`` so tests can assert exactly when vision was consulted
    and on what page image.
    """
    iterator = iter(transcripts)
    calls: list[Path] = []

    def _fake(*, image_path: Path) -> VisionTranscript:
        calls.append(image_path)
        return next(iterator)

    _fake.calls = calls  # type: ignore[attr-defined]
    return _fake


class TestVisionFallbackNotConsulted:
    def test_first_attempt_accept_skips_vision(self, job):
        # Plan acceptance criterion: "No vision call is made on pages that
        # already accept on first OCR attempt." Stub would raise on call.
        vision = _stub_vision([])

        result = run_page(
            job,
            1,
            ocr=clean_ocr,
            spellcheck=no_errors,
            vision_transcriber=vision,
        )

        assert result.decision == "accept"
        assert vision.calls == []
        assert load_page(job, 1).vision_transcript is None

    def test_diagnostician_accept_skips_vision(self, job):
        diagnostician = _stub_diagnostician([])
        vision = _stub_vision([])

        result = run_page(
            job,
            1,
            ocr=clean_ocr,
            spellcheck=no_errors,
            diagnostician=diagnostician,
            vision_transcriber=vision,
        )

        assert result.decision == "accept"
        assert vision.calls == []

    def test_no_vision_callable_preserves_pre_t07_behavior(self, job):
        # A garbled page with no vision callable must still surface as
        # needs_review without writing vision files. This guards callers that
        # don't opt in to vision yet.
        result = run_page(
            job,
            1,
            ocr=garbled_ocr,
            spellcheck=no_errors,
            vision_transcriber=None,
        )

        assert result.decision == "needs_review"
        page = load_page(job, 1)
        assert page.vision_transcript is None
        assert page.vision_quality is None


class TestVisionFallbackAfterAttemptsExhausted:
    def test_vision_accept_finalizes_page(self, job):
        # BDRC attempts all return garbled text; vision returns a clean Tibetan
        # transcript. The page must finalize from vision, write vision_ocr.json,
        # and tag the notes so the reviewer sees which engine produced final.txt.
        diagnostician = _stub_diagnostician(
            [
                RetryWithSettings(settings_overrides={"k_factor": 3.0}, rationale="x"),
                RetryWithSettings(settings_overrides={"k_factor": 4.0}, rationale="y"),
            ]
        )
        vision = _stub_vision([VisionTranscript(text=CLEAN_TEXT, notes=None)])

        result = run_page(
            job,
            1,
            ocr=garbled_ocr,
            spellcheck=no_errors,
            diagnostician=diagnostician,
            vision_transcriber=vision,
            max_attempts=3,
        )

        assert result.decision == "accept"
        assert len(vision.calls) == 1
        # final.txt is the vision transcript, not the last garbled BDRC attempt.
        assert (job.root / "page-001" / "final.txt").read_text() == CLEAN_TEXT
        page = load_page(job, 1)
        assert page.final_text == CLEAN_TEXT
        assert page.vision_transcript == {"text": CLEAN_TEXT}
        # Notes record the provenance so it doesn't get mistaken for a BDRC accept.
        assert "vision fallback" in (page.notes or "")

    def test_vision_failure_attaches_to_needs_review(self, job):
        # Vision also returns garbled text → page surfaces as needs_review but
        # both reads are persisted side-by-side. The acceptance criterion:
        # "Vision transcript is scored and either accepted or attached to the
        # human-review record."
        diagnostician = _stub_diagnostician(
            [RetryWithSettings(settings_overrides={"k_factor": 3.0}, rationale="x")]
        )
        vision = _stub_vision([VisionTranscript(text=GARBLED_TEXT, notes="hard to read")])

        result = run_page(
            job,
            1,
            ocr=garbled_ocr,
            spellcheck=no_errors,
            diagnostician=diagnostician,
            vision_transcriber=vision,
            max_attempts=2,
        )

        assert result.decision == "needs_review"
        assert result.page.final_text is None
        assert not (job.root / "page-001" / "final.txt").is_file()
        page = load_page(job, 1)
        assert page.vision_transcript == {"text": GARBLED_TEXT, "notes": "hard to read"}
        assert page.vision_quality is not None
        # BDRC attempts list is also preserved — both engines visible to reviewer.
        assert len(page.attempts) == 2

    def test_vision_runs_without_diagnostician(self, job):
        # Vision can be wired in independently of the diagnostician: a one-shot
        # OCR that fails should still trigger vision before declaring needs_review.
        vision = _stub_vision([VisionTranscript(text=CLEAN_TEXT)])

        result = run_page(
            job,
            1,
            ocr=garbled_ocr,
            spellcheck=no_errors,
            vision_transcriber=vision,
        )

        assert result.decision == "accept"
        assert len(vision.calls) == 1
        assert load_page(job, 1).final_text == CLEAN_TEXT


class TestVisionFallbackAfterNeedsHuman:
    def test_needs_human_still_consults_vision(self, job):
        # The diagnostician flagging NeedsHuman means BDRC retries won't help.
        # Vision is a different engine and gets one shot. Here it succeeds, so
        # the page finalizes from vision even though Claude flagged it.
        diagnostician = _stub_diagnostician(
            [NeedsHuman(reason="multi-column layout")]
        )
        vision = _stub_vision([VisionTranscript(text=CLEAN_TEXT)])

        result = run_page(
            job,
            1,
            ocr=garbled_ocr,
            spellcheck=no_errors,
            diagnostician=diagnostician,
            vision_transcriber=vision,
            max_attempts=3,
        )

        assert result.decision == "accept"
        page = load_page(job, 1)
        assert page.final_text == CLEAN_TEXT
        # The diagnostician's reason is preserved in notes so the reviewer
        # sees why vision was consulted, even on an accept.
        assert "multi-column layout" in (page.notes or "")

    def test_needs_human_with_no_vision_returns_needs_review(self, job):
        # No vision callable → NeedsHuman is still terminal.
        diagnostician = _stub_diagnostician(
            [NeedsHuman(reason="torn page")]
        )

        result = run_page(
            job,
            1,
            ocr=garbled_ocr,
            spellcheck=no_errors,
            diagnostician=diagnostician,
            max_attempts=3,
        )

        assert result.decision == "needs_review"
        page = load_page(job, 1)
        assert page.vision_transcript is None


class TestRunAllPagesPassesVision:
    def test_vision_called_only_on_failing_pages(self, job):
        # Page 1 and 3 OCR cleanly; page 2 garbled. Vision must run on page 2
        # only — not on the accepts. Then the batch finalizes all three.
        vision = _stub_vision([VisionTranscript(text=CLEAN_TEXT)])

        def mixed_ocr(image_path: Path, settings: dict) -> OcrResult:
            if image_path.parent.name == "page-002":
                return OcrResult(text=GARBLED_TEXT, line_count=1)
            return OcrResult(text=CLEAN_TEXT, line_count=2)

        results = run_all_pages(
            job,
            ocr=mixed_ocr,
            spellcheck=no_errors,
            vision_transcriber=vision,
        )

        assert {r.page.index: r.decision for r in results} == {
            1: "accept",
            2: "accept",
            3: "accept",
        }
        assert len(vision.calls) == 1
        assert vision.calls[0].parent.name == "page-002"
