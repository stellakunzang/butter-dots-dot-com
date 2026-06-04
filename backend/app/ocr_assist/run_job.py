"""
CLI entry point for the interactive OCR runner.

Usage::

    python -m app.ocr_assist.run_job <pdf_path> [--jobs-root DIR] [--model NAME]

Creates a fresh job under ``--jobs-root`` (default ``./jobs``), renders the
PDF to per-page PNGs, then runs every page through ``runner.run_page``.
Prints a summary of how each page resolved: ``accept`` or ``needs_review``.

This is a smoke-test surface for T-05. The interactive UI lands in T-09.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from app.ocr_assist.job_store import create_job
from app.ocr_assist.runner import RunResult, run_all_pages


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run interactive OCR on a PDF.")
    parser.add_argument("pdf_path", type=Path, help="Path to the source PDF.")
    parser.add_argument(
        "--jobs-root",
        type=Path,
        default=Path("./jobs"),
        help="Directory to hold per-job state (default: ./jobs).",
    )
    parser.add_argument(
        "--model",
        default="Modern",
        help="Baseline OCR model variant to record on the job (default: Modern).",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose logging."
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if not args.pdf_path.is_file():
        print(f"error: PDF not found at {args.pdf_path}", file=sys.stderr)
        return 1

    args.jobs_root.mkdir(parents=True, exist_ok=True)
    pdf_bytes = args.pdf_path.read_bytes()
    job = create_job(
        pdf_bytes,
        source_file=str(args.pdf_path),
        baseline_settings={"model_variant": args.model},
        jobs_root=args.jobs_root,
    )
    print(f"created job {job.id} with {job.page_count} pages → {job.root}")

    results = run_all_pages(job)
    _print_summary(results)
    return 0


def _print_summary(results: list[RunResult]) -> None:
    accepted = sum(1 for r in results if r.decision == "accept")
    needs_review = sum(1 for r in results if r.decision == "needs_review")
    print(f"\nrun complete: {accepted} accepted, {needs_review} needs review")
    for r in results:
        score = r.quality.composite_score
        print(f"  page {r.page.index:>3}: {r.decision:<13} composite={score:.3f}")


if __name__ == "__main__":
    raise SystemExit(main())
