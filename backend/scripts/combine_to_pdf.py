#!/usr/bin/env python3
"""Combine image and PDF files in a folder into a single PDF."""

from __future__ import annotations

import argparse
import io
import re
from pathlib import Path

from PIL import Image
from pypdf import PdfReader, PdfWriter


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp"}
PDF_SUFFIXES = {".pdf"}


def natural_key(path: Path) -> list[object]:
    parts = re.split(r"(\d+)", path.name.lower())
    return [int(part) if part.isdigit() else part for part in parts]


def image_to_pdf_bytes(path: Path) -> bytes:
    with Image.open(path) as image:
        if image.mode in ("RGBA", "LA", "P"):
            image = image.convert("RGB")
        elif image.mode != "RGB":
            image = image.convert("RGB")
        buffer = io.BytesIO()
        image.save(buffer, format="PDF")
        return buffer.getvalue()


def append_file(writer: PdfWriter, path: Path) -> None:
    suffix = path.suffix.lower()
    if suffix in PDF_SUFFIXES:
        reader = PdfReader(str(path))
        for page in reader.pages:
            writer.add_page(page)
        return
    if suffix in IMAGE_SUFFIXES:
        reader = PdfReader(io.BytesIO(image_to_pdf_bytes(path)))
        for page in reader.pages:
            writer.add_page(page)
        return
    raise ValueError(f"Unsupported file type: {path.name}")


def combine_folder(input_dir: Path, output_path: Path) -> list[Path]:
    files = sorted(
        [
            path
            for path in input_dir.iterdir()
            if path.is_file() and not path.name.startswith(".")
        ],
        key=natural_key,
    )
    if not files:
        raise SystemExit(f"No files found in {input_dir}")

    writer = PdfWriter()
    for path in files:
        append_file(writer, path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as handle:
        writer.write(handle)

    return files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", type=Path, help="Folder containing pages to combine")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("pages_for_ocr_test.pdf"),
        help="Output PDF path (default: pages_for_ocr_test.pdf)",
    )
    args = parser.parse_args()

    if not args.input_dir.is_dir():
        raise SystemExit(f"Input folder not found: {args.input_dir}")

    files = combine_folder(args.input_dir, args.output)
    print(f"Combined {len(files)} files into {args.output.resolve()}")
    for path in files:
        print(f"  - {path.name}")


if __name__ == "__main__":
    main()
