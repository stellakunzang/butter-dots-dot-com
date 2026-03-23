"""
BDRC OCR adapter.

Wraps the BDRC/Monlam OCRPipeline (MIT licensed) as a simple server-side
interface. The pipeline is loaded once at module import time as a singleton
so model weights are only read from disk on the first use.

Source: https://github.com/buda-base/tibetan-ocr-app
"""
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from app.config import settings

logger = logging.getLogger(__name__)

# Paths relative to backend/ root
BACKEND_DIR = Path(__file__).parent.parent.parent
MODELS_DIR = BACKEND_DIR / "Models"
OCR_MODELS_DIR = BACKEND_DIR / "OCRModels"


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

    def run_on_image(self, image: np.ndarray) -> list[OCRLine]:
        """
        Run OCR on a single page image (numpy array in BGR format, as from cv2).
        Returns a list of OCRLine objects ordered top-to-bottom.
        """
        if not self.ready:
            raise RuntimeError(self._error or "OCR engine not ready")

        from BDRC.Data import Encoding, OpStatus

        status, result = self._pipeline.run_ocr(
            image=image,
            k_factor=2.5,
            bbox_tolerance=3.0,
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


# Module-level singleton — loaded on first use
_engine: Optional[BDRCOCREngine] = None


def get_engine() -> BDRCOCREngine:
    global _engine
    if _engine is None:
        _engine = BDRCOCREngine()
    return _engine
