"""Shared helpers for Anthropic-backed OCR assist providers."""
from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any


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


def anthropic_image_block(
    image_path: Path, *, cache_control: dict[str, str] | None = None
) -> dict[str, Any]:
    image_b64, media_type = encode_image_base64(image_path)
    block: dict[str, Any] = {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": image_b64,
        },
    }
    if cache_control is not None:
        block["cache_control"] = cache_control
    return block


def anthropic_tools_with_cache(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Copy ``tools`` and attach ephemeral cache control to the last entry."""
    copied = [dict(tool) for tool in tools]
    copied[-1] = {**copied[-1], "cache_control": {"type": "ephemeral"}}
    return copied


def log_anthropic_usage(logger: logging.Logger, usage: Any, *, label: str) -> None:
    if usage is None:
        return
    logger.info(
        "%s usage: input=%s cache_read=%s cache_create=%s output=%s",
        label,
        getattr(usage, "input_tokens", "?"),
        getattr(usage, "cache_read_input_tokens", "?"),
        getattr(usage, "cache_creation_input_tokens", "?"),
        getattr(usage, "output_tokens", "?"),
    )
