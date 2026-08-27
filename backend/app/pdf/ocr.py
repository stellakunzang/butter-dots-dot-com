"""
BDRC OCR adapter.

Wraps the BDRC/Monlam OCRPipeline (MIT licensed) as a simple server-side
interface. The pipeline is loaded once at module import time as a singleton
so model weights are only read from disk on the first use.

Per-page settings (``k_factor``, ``bbox_tolerance``, ``model_variant``,
``rotate``) from the interactive OCR job store are accepted by
``run_on_image`` and forwarded into ``OCRPipeline.run_ocr``. Model variants
are loaded on demand and swapped via ``update_ocr_model``.

Source: https://github.com/buda-base/tibetan-ocr-app
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np
from app.config import settings
from app.pdf.ocr_settings import (
    OcrRunSettings,
    apply_manual_rotation,
    parse_ocr_settings,
)

logger = logging.getLogger(__name__)

# Paths relative to backend/ root
BACKEND_DIR = Path(__file__).parent.parent.parent
MODELS_DIR = BACKEND_DIR / "Models"
OCR_MODELS_DIR = BACKEND_DIR / "OCRModels"


def _normalize_to_bgr(image: np.ndarray) -> np.ndarray:
    """Coerce a page image into 3-channel BGR.

    Handles grayscale (h,w), BGRA (h,w,4), and exotic formats (e.g. CMYK+Alpha)
    by falling back through PIL. Already-BGR inputs pass through untouched.
    """
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    if image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    if image.shape[2] != 3:
        from PIL import Image as PILImage
        pil_img = PILImage.fromarray(image).convert("RGB")
        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    return image


@dataclass
class OCRLine:
    """A single recognized line of text with its bounding box in image coordinates."""
    text: str
    x: int
    y: int
    width: int
    height: int


class BDRCOCREngine:
    """
    Singleton wrapper around BDRC OCRPipeline.
    Call get_engine() to get the shared instance.
    """

    def __init__(self):
        self._pipeline = None
        self._ready = False
        self._error: Optional[str] = None
        self._active_model_name: str | None = None
        self._model_config_cache: dict[str, Any] = {}

    def _load(self) -> None:
        """Load the ONNX models. Called lazily on first use."""
        try:
            from BDRC.Inference import OCRPipeline
            from BDRC.Data import Encoding, LineDetectionConfig, Platform
            from BDRC.Utils import import_local_model, get_platform, read_ocr_model_config

            platform = get_platform()

            # Line detection model
            line_model_file = MODELS_DIR / "Lines" / "PhotiLines.onnx"
            if not line_model_file.exists():
                self._error = (
                    f"Line detection model not found at {line_model_file}. "
                    "Run: python scripts/download_models.py"
                )
                logger.error(self._error)
                return

            line_config = LineDetectionConfig(
                model_file=str(line_model_file),
                patch_size=512,
            )

            # OCR model — configured via OCR_MODEL_NAME env var / .env
            model_name = settings.ocr_model_name
            ocr_model_dir = OCR_MODELS_DIR / model_name
            if not ocr_model_dir.exists():
                self._error = (
                    f"OCR model '{model_name}' not found at {ocr_model_dir}. "
                    "Run: python scripts/download_models.py"
                )
                logger.error(self._error)
                return

            ocr_model = import_local_model(str(ocr_model_dir))
            if ocr_model is None:
                self._error = f"Failed to load OCR model from {ocr_model_dir}"
                logger.error(self._error)
                return

            self._pipeline = OCRPipeline(platform, ocr_model.config, line_config)
            self._active_model_name = model_name
            self._model_config_cache[model_name] = ocr_model.config
            self._ready = True
            logger.info(
                "BDRC OCR pipeline ready (model=%s, line_detection=%s)",
                model_name,
                line_model_file.name,
            )

        except Exception as e:
            self._error = f"Failed to initialize OCR pipeline: {e}"
            logger.exception(self._error)

    @property
    def ready(self) -> bool:
        if not self._ready and self._error is None:
            self._load()
        return self._ready

    @property
    def error(self) -> Optional[str]:
        return self._error

    def run_on_image(
        self,
        image: np.ndarray,
        page_settings: dict[str, Any] | None = None,
    ) -> list[OCRLine]:
        """
        Run OCR on a single page image (numpy array in BGR format, as from cv2).

        ``page_settings`` is the per-page dict from the interactive OCR job
        store (``settings.json``). When omitted, defaults match the legacy
        hardcoded run (``k_factor=2.5``, ``bbox_tolerance=3.0``, env
        ``OCR_MODEL_NAME`` for the model).

        Returns a list of OCRLine objects ordered top-to-bottom.
        """
        if not self.ready:
            raise RuntimeError(self._error or "OCR engine not ready")

        run_settings = parse_ocr_settings(
            page_settings, fallback_model=settings.ocr_model_name
        )
        self._ensure_ocr_model(run_settings.model_name)

        image = _normalize_to_bgr(image)
        image = apply_manual_rotation(image, run_settings.rotate)

        from BDRC.Data import Encoding, OpStatus

        status, result = self._pipeline.run_ocr(
            image=image,
            k_factor=run_settings.k_factor,
            bbox_tolerance=run_settings.bbox_tolerance,
            merge_lines=True,
            use_tps=False,
            target_encoding=Encoding.Unicode,
        )

        if status != OpStatus.SUCCESS:
            logger.warning("OCR returned non-success status: %s — %s", status, result)
            return []

        _rot_mask, sorted_lines, ocr_lines, _angle = result

        output: list[OCRLine] = []
        for line_data, ocr_line in zip(sorted_lines, ocr_lines):
            bbox = line_data.bbox
            output.append(
                OCRLine(
                    text=ocr_line.text.strip(),
                    x=bbox.x,
                    y=bbox.y,
                    width=bbox.w,
                    height=bbox.h,
                )
            )

        return output

    def _ensure_ocr_model(self, model_name: str) -> None:
        """Load and activate ``model_name`` if it differs from the current one."""
        if self._active_model_name == model_name:
            return

        config = self._load_model_config(model_name)
        if config is None:
            logger.warning(
                "OCR model %r not available; keeping active model %r",
                model_name,
                self._active_model_name,
            )
            return

        self._pipeline.update_ocr_model(config)
        self._active_model_name = model_name
        logger.info("Switched BDRC OCR model to %s", model_name)

    def _load_model_config(self, model_name: str) -> Any | None:
        if model_name in self._model_config_cache:
            return self._model_config_cache[model_name]

        model_dir = OCR_MODELS_DIR / model_name
        if not model_dir.is_dir():
            logger.warning("OCR model directory not found: %s", model_dir)
            return None

        from BDRC.Utils import import_local_model

        ocr_model = import_local_model(str(model_dir))
        if ocr_model is None:
            logger.warning("Failed to load OCR model from %s", model_dir)
            return None

        self._model_config_cache[model_name] = ocr_model.config
        return ocr_model.config


# Module-level singleton — loaded on first use
_engine: Optional[BDRCOCREngine] = None


def get_engine() -> BDRCOCREngine:
    global _engine
    if _engine is None:
        _engine = BDRCOCREngine()
    return _engine
