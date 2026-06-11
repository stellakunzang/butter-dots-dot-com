"""Vendor-agnostic helpers for reading page images on disk."""
from __future__ import annotations

import base64
from pathlib import Path


def guess_media_type(image_path: Path) -> str:
    suffix = image_path.suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }.get(suffix, "image/png")


def encode_image_base64(image_path: Path) -> tuple[str, str]:
    """Return ``(base64_data, media_type)`` for an on-disk page image."""
    image_bytes = image_path.read_bytes()
    return base64.standard_b64encode(image_bytes).decode("ascii"), guess_media_type(
        image_path
    )
