"""
CLI entry point for the interactive OCR runner.

Usage::

    python -m app.ocr_assist.run_job <pdf_path> [--jobs-root DIR] [--model NAME]
    python -m app.ocr_assist.run_job book.pdf --pages 3,7,12
    python -m app.ocr_assist.run_job --job-id <id> --rerun-pages 7
    python -m app.ocr_assist.run_job book.pdf --enable-ai

Creates a fresh job under ``--jobs-root`` (default ``./jobs``), or loads an
existing job via ``--job-id``, then runs pages through ``runner.run_page``.
Default path is BDRC + quality scorer only (no LLM). Prints a summary of how
each page resolved: ``accept``, ``needs_review``, or ``error``.

Provider selection (when ``--enable-ai`` is set — CLI experiment only):
  ``DIAGNOSTICIAN_PROVIDER`` / ``--diagnostician-provider`` — default ``anthropic``
  ``VISION_OCR_PROVIDER`` / ``--vision-provider`` — ``anthropic`` or ``gemini``
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from app.config import settings
from app.ocr_assist.job_store import create_job, load_job, reset_page, OUTPUT_DOCX_FILE, Job
from app.ocr_assist.providers import build_diagnostician, build_vision_transcriber
from app.ocr_assist.providers.credentials import resolve_anthropic_api_key, resolve_gemini_api_key
from app.ocr_assist.runner import (
    DEFAULT_MAX_ATTEMPTS,
    DEFAULT_THRESHOLDS,
    RunResult,
    run_all_pages,
)
from app.ocr_assist.quality import Thresholds


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run interactive OCR on a PDF.")
    parser.add_argument(
        "pdf_path",
        type=Path,
        nargs="?",
        default=None,
        help="Path to the source PDF (required unless --job-id is set).",
    )
    parser.add_argument(
        "--jobs-root",
        type=Path,
        default=Path("./jobs"),
        help="Directory to hold per-job state (default: ./jobs).",
    )
    parser.add_argument(
        "--job-id",
        default=None,
        help="Load an existing job under --jobs-root instead of creating one.",
    )
    parser.add_argument(
        "--pages",
        default=None,
        help="Comma-separated 1-based page numbers to run (e.g. 3,7,12).",
    )
    parser.add_argument(
        "--rerun-pages",
        default=None,
        help=(
            "Comma-separated 1-based pages to reset (clear finals) then run. "
            "Requires --job-id. Keeps prior attempts/settings by default."
        ),
    )
    parser.add_argument(
        "--model",
        default=settings.ocr_model_name,
        help=(
            "Baseline OCR model variant to record on a new job "
            f"(default: {settings.ocr_model_name} from OCR_MODEL_NAME)."
        ),
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=DEFAULT_MAX_ATTEMPTS,
        help=f"Max BDRC/diagnostician attempts per page (default: {DEFAULT_MAX_ATTEMPTS}).",
    )
    parser.add_argument(
        "--enable-ai",
        action="store_true",
        help=(
            "Wire in AI diagnostician + vision fallback (CLI experiment). "
            "Not used by the local QA UI bulk path."
        ),
    )
    parser.add_argument(
        "--diagnostician-provider",
        default=os.environ.get("DIAGNOSTICIAN_PROVIDER", "anthropic"),
        help="Diagnostician backend (default: anthropic, or DIAGNOSTICIAN_PROVIDER).",
    )
    parser.add_argument(
        "--vision-provider",
        default=os.environ.get("VISION_OCR_PROVIDER", "anthropic"),
        help="Vision OCR backend: anthropic or gemini (default: anthropic).",
    )
    parser.add_argument(
        "--threshold-accept",
        type=float,
        default=DEFAULT_THRESHOLDS.accept,
        help=(
            "Composite score at or above which a page auto-accepts "
            f"(default: {DEFAULT_THRESHOLDS.accept})."
        ),
    )
    parser.add_argument(
        "--threshold-reject",
        type=float,
        default=DEFAULT_THRESHOLDS.reject,
        help=(
            "Composite score below which a page rejects without retry "
            f"(default: {DEFAULT_THRESHOLDS.reject})."
        ),
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose logging."
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.rerun_pages and not args.job_id:
        print("error: --rerun-pages requires --job-id", file=sys.stderr)
        return 1
    if args.job_id is None and args.pdf_path is None:
        print("error: pdf_path is required unless --job-id is set", file=sys.stderr)
        return 1
    if args.max_attempts < 1:
        print("error: --max-attempts must be >= 1", file=sys.stderr)
        return 1

    try:
        thresholds = Thresholds(accept=args.threshold_accept, reject=args.threshold_reject)
    except ValueError as exc:
        print(f"error: invalid thresholds: {exc}", file=sys.stderr)
        return 1

    try:
        pages = _parse_page_list(args.pages) if args.pages else None
        rerun_pages = _parse_page_list(args.rerun_pages) if args.rerun_pages else None
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    args.jobs_root = args.jobs_root.expanduser().resolve()
    args.jobs_root.mkdir(parents=True, exist_ok=True)

    if args.job_id:
        try:
            job = load_job(args.jobs_root, args.job_id)
        except FileNotFoundError:
            print(
                f"error: job {args.job_id!r} not found under {args.jobs_root}",
                file=sys.stderr,
            )
            return 1
        _print_job_banner("loaded", job)
    else:
        assert args.pdf_path is not None
        if not args.pdf_path.is_file():
            print(f"error: PDF not found at {args.pdf_path}", file=sys.stderr)
            return 1
        pdf_bytes = args.pdf_path.read_bytes()
        job = create_job(
            pdf_bytes,
            source_file=str(args.pdf_path.resolve()),
            baseline_settings={"model_variant": args.model},
            jobs_root=args.jobs_root,
        )
        _print_job_banner("created", job)

    if rerun_pages is not None:
        for index in rerun_pages:
            if index < 1 or index > job.page_count:
                print(
                    f"error: --rerun-pages index {index} out of range "
                    f"(job has {job.page_count} pages)",
                    file=sys.stderr,
                )
                return 1
            reset_page(job, index)
            print(f"reset page {index} (finals cleared; attempts/settings kept)")

    # Rerun implies those pages; --pages can further restrict a new/loaded job.
    if rerun_pages is not None and pages is None:
        page_indices = rerun_pages
    elif pages is not None and rerun_pages is not None:
        page_indices = [p for p in pages if p in set(rerun_pages)] or rerun_pages
    else:
        page_indices = pages

    diagnostician = None
    vision_transcriber = None
    if args.enable_ai:
        diag_provider = args.diagnostician_provider.strip().lower()
        vision_provider = args.vision_provider.strip().lower()
        if diag_provider in {"anthropic", "claude"} and not resolve_anthropic_api_key():
            print(
                "error: ANTHROPIC_API_KEY not set (export it or add to backend/.env)",
                file=sys.stderr,
            )
            return 1
        if vision_provider in {"anthropic", "claude"} and not resolve_anthropic_api_key():
            print(
                "error: ANTHROPIC_API_KEY not set for vision provider "
                "(export it or add to backend/.env)",
                file=sys.stderr,
            )
            return 1
        if vision_provider in {"gemini", "google"} and not resolve_gemini_api_key():
            print(
                "error: GEMINI_API_KEY or GOOGLE_API_KEY not set "
                "(export it or add GEMINI_API_KEY to backend/.env)",
                file=sys.stderr,
            )
            return 1
        diagnostician = build_diagnostician(args.diagnostician_provider)
        vision_transcriber = build_vision_transcriber(args.vision_provider)
        print(
            f"AI enabled: diagnostician={args.diagnostician_provider}, "
            f"vision={args.vision_provider}"
        )

    try:
        results = run_all_pages(
            job,
            thresholds=thresholds,
            max_attempts=args.max_attempts,
            diagnostician=diagnostician,
            vision_transcriber=vision_transcriber,
            page_indices=page_indices,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    _print_summary(results, job=job)
    return 0


def _parse_page_list(raw: str) -> list[int]:
    """Parse ``'3,7,12'`` into a list of positive ints."""
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if not parts:
        raise ValueError("page list must not be empty")
    pages: list[int] = []
    for part in parts:
        try:
            n = int(part)
        except ValueError as exc:
            raise ValueError(f"invalid page number {part!r}") from exc
        if n < 1:
            raise ValueError(f"page numbers must be >= 1 (got {n})")
        pages.append(n)
    return pages


def _job_root_abs(job: Job) -> Path:
    return job.root.expanduser().resolve()


def _print_job_banner(verb: str, job: Job) -> None:
    """Print job id + absolute paths so CLI output is easy to find later."""
    root = _job_root_abs(job)
    print(f"{verb} job")
    print(f"  job-id:     {job.id}")
    print(f"  pages:      {job.page_count}")
    print(f"  directory:  {root}")
    print(f"  docx (when pages finalize):  {root / OUTPUT_DOCX_FILE}")


def _print_summary(results: list[RunResult], *, job: Job | None = None) -> None:
    accepted = sum(1 for r in results if r.decision == "accept")
    needs_review = sum(1 for r in results if r.decision == "needs_review")
    errored = sum(1 for r in results if r.decision == "error")
    print(
        f"\nrun complete: {accepted} accepted, {needs_review} needs review, "
        f"{errored} error"
    )
    for r in results:
        if r.quality is None:
            print(f"  page {r.page.index:>3}: {r.decision:<13} error={r.error}")
        else:
            score = r.quality.composite_score
            print(f"  page {r.page.index:>3}: {r.decision:<13} composite={score:.3f}")

    if job is None:
        return
    root = _job_root_abs(job)
    docx_path = root / OUTPUT_DOCX_FILE
    print("\nartifacts")
    print(f"  job-id:     {job.id}")
    print(f"  directory:  {root}")
    if docx_path.is_file():
        print(f"  docx:       {docx_path}")
    else:
        print(
            f"  docx:       (not written yet — no finalized pages; "
            f"expected at {docx_path})"
        )

if __name__ == "__main__":
    raise SystemExit(main())
