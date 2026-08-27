"""Vendor-agnostic helpers for reading page images on disk."""
from __future__ import annotations

import base64
import io
import logging
from pathlib import Path

from PIL import Image


logger = logging.getLogger(__name__)


def guess_media_type(image_path: Path) -> str:
    suffix = image_path.suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }.get(suffix, "image/png")


def load_image_bytes(
    image_path: Path, *, max_dimension: int | None = None
) -> tuple[bytes, str]:
    """Return ``(image_bytes, media_type)``, downscaling when ``max_dimension`` is set."""
    media_type = guess_media_type(image_path)
    if max_dimension is None:
        return image_path.read_bytes(), media_type

    try:
        with Image.open(image_path) as image:
            width, height = image.size
            longest = max(width, height)
            if longest <= max_dimension:
                return image_path.read_bytes(), media_type

            scale = max_dimension / longest
            new_size = (
                max(int(width * scale), 1),
                max(int(height * scale), 1),
            )
            logger.info(
                "Downscaling %s from %sx%s to %sx%s for API upload (max=%spx)",
                image_path.name,
                width,
                height,
                new_size[0],
                new_size[1],
                max_dimension,
            )
            resized = image.convert("RGB").resize(new_size, Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            resized.save(buffer, format="PNG")
            return buffer.getvalue(), "image/png"
    except (OSError, Image.UnidentifiedImageError):
        logger.warning(
            "Could not read dimensions from %s; sending original bytes to API",
            image_path,
        )
        return image_path.read_bytes(), media_type


def encode_image_base64(
    image_path: Path, *, max_dimension: int | None = None
) -> tuple[str, str]:
    """Return ``(base64_data, media_type)`` for an on-disk page image."""
    image_bytes, media_type = load_image_bytes(
        image_path, max_dimension=max_dimension
    )
    return base64.standard_b64encode(image_bytes).decode("ascii"), media_type
