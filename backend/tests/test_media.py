"""Tests for OCR assist image upload helpers."""
from __future__ import annotations

import base64
import io
from pathlib import Path

from PIL import Image

from app.ocr_assist.providers.anthropic_common import (
    ANTHROPIC_MAX_IMAGE_DIMENSION,
    anthropic_image_block,
)
from app.ocr_assist.providers.media import encode_image_base64, load_image_bytes


def _write_png(path: Path, size: tuple[int, int]) -> None:
    Image.new("RGB", size, color="white").save(path, format="PNG")


class TestLoadImageBytes:
    def test_small_image_passes_through_unchanged(self, tmp_path: Path) -> None:
        image_path = tmp_path / "small.png"
        _write_png(image_path, (100, 200))
        original = image_path.read_bytes()

        data, media_type = load_image_bytes(
            image_path, max_dimension=ANTHROPIC_MAX_IMAGE_DIMENSION
        )

        assert data == original
        assert media_type == "image/png"

    def test_oversized_image_is_downscaled(self, tmp_path: Path) -> None:
        image_path = tmp_path / "wide.png"
        _write_png(image_path, (18267, 4134))

        data, media_type = load_image_bytes(
            image_path, max_dimension=ANTHROPIC_MAX_IMAGE_DIMENSION
        )

        assert media_type == "image/png"
        with Image.open(io.BytesIO(data)) as resized:
            width, height = resized.size
        assert max(width, height) <= ANTHROPIC_MAX_IMAGE_DIMENSION
        assert width == ANTHROPIC_MAX_IMAGE_DIMENSION
        assert height == int(4134 * ANTHROPIC_MAX_IMAGE_DIMENSION / 18267)


class TestEncodeImageBase64:
    def test_anthropic_image_block_respects_dimension_limit(
        self, tmp_path: Path
    ) -> None:
        image_path = tmp_path / "wide.png"
        _write_png(image_path, (18267, 4134))

        block = anthropic_image_block(image_path)
        raw = base64.standard_b64decode(block["source"]["data"])
        with Image.open(io.BytesIO(raw)) as resized:
            width, height = resized.size

        assert block["source"]["media_type"] == "image/png"
        assert max(width, height) <= ANTHROPIC_MAX_IMAGE_DIMENSION

        _, media_type = encode_image_base64(
            image_path, max_dimension=ANTHROPIC_MAX_IMAGE_DIMENSION
        )
        assert media_type == "image/png"
