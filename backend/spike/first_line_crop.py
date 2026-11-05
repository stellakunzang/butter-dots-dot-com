"""Dump line boxes + try inner-box crops on the two stills (issue #79)."""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

from app.pdf.ocr import get_engine
from BDRC.Data import Encoding, OpStatus
from BDRC.line_detection import (
    build_line_data,
    build_raw_line_data,
    extract_line_images,
    filter_line_contours,
    sort_lines_by_threshold2,
)

OUT = Path(__file__).parent / "out"
K_FACTOR = 2.5
BBOX_TOLERANCE = 3.0


def dump_lines(stem: str, image: np.ndarray) -> None:
    engine = get_engine()
    if not engine.ready:
        raise RuntimeError(engine.error)
    pipeline = engine._pipeline
    line_mask = pipeline.line_inference.predict(image)
    rot_img, rot_mask, contours, angle = build_raw_line_data(image, line_mask)
    filtered = filter_line_contours(rot_mask, contours)
    line_data = [build_line_data(x) for x in filtered]
    sorted_lines, _ = sort_lines_by_threshold2(rot_mask, line_data, group_lines=True)
    line_images = extract_line_images(rot_img, sorted_lines, K_FACTOR, BBOX_TOLERANCE)

    print(f"\n{stem}: {len(sorted_lines)} lines, angle={angle:.2f}")
    dest = OUT / f"{stem}-lines"
    dest.mkdir(parents=True, exist_ok=True)
    for i, (line, crop) in enumerate(zip(sorted_lines, line_images), start=1):
        b = line.bbox
        print(f"  line {i}: x={b.x:4} y={b.y:4} w={b.w:4} h={b.h:3} crop={crop.shape[1]}x{crop.shape[0]}")
        cv2.imwrite(str(dest / f"line-{i:02}.png"), crop)


def inner_text_crop(image: np.ndarray) -> np.ndarray:
    """Keep the inner text block: drop table, pecha frame, and side labels.

    Strategy: find the bright paper strip, then inset a fraction of its size
    to skip the inked border and the vertical running titles.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, paper = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
    paper = cv2.morphologyEx(paper, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    contours, _ = cv2.findContours(paper, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise RuntimeError("no paper region found")
    x, y, w, h = cv2.boundingRect(max(contours, key=cv2.contourArea))
    # Inset: sides lose more (vertical titles), top/bottom lose the frame rule.
    inset_x = int(w * 0.08)
    inset_y = int(h * 0.18)
    x1, y1 = x + inset_x, y + inset_y
    x2, y2 = x + w - inset_x, y + h - inset_y
    print(f"  paper=({x},{y},{w},{h}) inner=({x1},{y1})-({x2},{y2})")
    return image[y1:y2, x1:x2]


def ocr_text(image: np.ndarray) -> str:
    engine = get_engine()
    lines = engine.run_on_image(image, page_settings={"model_variant": "Woodblock"})
    return "\n".join(line.text for line in lines if line.text)


def main(paths: list[str]) -> None:
    OUT.mkdir(exist_ok=True)
    get_engine()  # load once
    for raw in paths:
        path = Path(raw)
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        print(f"\n=== {path.name} {image.shape[1]}x{image.shape[0]} ===")
        dump_lines(path.stem, image)

        cropped = inner_text_crop(image)
        crop_path = OUT / f"{path.stem}.inner.png"
        cv2.imwrite(str(crop_path), cropped)
        dump_lines(f"{path.stem}-inner", cropped)

        print("--- full still, first line ---")
        print((ocr_text(image).splitlines() or [""])[0])
        print("--- inner crop, first line ---")
        print((ocr_text(cropped).splitlines() or [""])[0])
        print("--- inner crop, all ---")
        print(ocr_text(cropped))


if __name__ == "__main__":
    main(sys.argv[1:])
