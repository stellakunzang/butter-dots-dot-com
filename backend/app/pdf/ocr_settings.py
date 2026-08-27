"""
Per-page OCR settings for the BDRC pipeline.

The interactive OCR workflow persists a settings dict on each page
(``settings.json``). This module resolves diagnostician-friendly aliases
(``Ume`` → ``Ume_Druma``) and supplies defaults so callers can pass the
dict straight through to ``BDRCOCREngine.run_on_image``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


DEFAULT_K_FACTOR = 2.5
DEFAULT_BBOX_TOLERANCE = 3.0

# Diagnostician tool schema uses short names; BDRC model dirs use these.
MODEL_VARIANT_ALIASES: dict[str, str] = {
    "Modern": "Modern",
    "Woodblock": "Woodblock",
    "Woodblock-Stacks": "Woodblock-Stacks",
    "Ume": "Ume_Druma",
    "Ume_Druma": "Ume_Druma",
    "Ume_Petsuk": "Ume_Petsuk",
}


@dataclass(frozen=True)
class OcrRunSettings:
    k_factor: float
    bbox_tolerance: float
    rotate: float
    model_name: str


def resolve_model_variant(variant: str | None, *, fallback: str) -> str:
    """Map a page's ``model_variant`` to a BDRC OCRModels directory name."""
    if not variant:
        return fallback
    key = variant.strip()
    if key in MODEL_VARIANT_ALIASES:
        return MODEL_VARIANT_ALIASES[key]
    # Allow passing through an exact directory name the diagnostician didn't
    # enumerate (e.g. Woodblock-Stacks).
    return key


def parse_ocr_settings(
    settings: dict[str, Any] | None,
    *,
    fallback_model: str,
) -> OcrRunSettings:
    """Coerce a page settings dict into typed run parameters."""
    raw = settings or {}
    k_factor = float(raw.get("k_factor", DEFAULT_K_FACTOR))
    bbox_tolerance = float(raw.get("bbox_tolerance", DEFAULT_BBOX_TOLERANCE))
    rotate = float(raw.get("rotate", 0.0))
    model_name = resolve_model_variant(raw.get("model_variant"), fallback=fallback_model)
    return OcrRunSettings(
        k_factor=k_factor,
        bbox_tolerance=bbox_tolerance,
        rotate=rotate,
        model_name=model_name,
    )


def apply_manual_rotation(image: np.ndarray, degrees_clockwise: float) -> np.ndarray:
    """Rotate a page image before OCR when auto line-detection skew isn't enough.

    The diagnostician documents positive degrees as clockwise; OpenCV's
    ``getRotationMatrix2D`` uses counter-clockwise for positive angles, so
    we negate here.
    """
    if degrees_clockwise == 0.0:
        return image
    from BDRC.line_detection import rotate_from_angle

    return rotate_from_angle(image, -degrees_clockwise)
