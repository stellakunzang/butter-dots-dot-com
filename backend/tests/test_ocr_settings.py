"""
Tests for per-page OCR settings parsing and model alias resolution.
"""
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.pdf.ocr_settings import (
    DEFAULT_BBOX_TOLERANCE,
    DEFAULT_K_FACTOR,
    OcrRunSettings,
    apply_manual_rotation,
    parse_ocr_settings,
    resolve_model_variant,
)


class TestResolveModelVariant:
    def test_diagnostician_aliases(self):
        assert resolve_model_variant("Modern", fallback="Woodblock") == "Modern"
        assert resolve_model_variant("Woodblock", fallback="Woodblock") == "Woodblock"
        assert resolve_model_variant("Ume", fallback="Woodblock") == "Ume_Druma"

    def test_exact_directory_names_pass_through(self):
        assert resolve_model_variant("Ume_Petsuk", fallback="Woodblock") == "Ume_Petsuk"
        assert (
            resolve_model_variant("Woodblock-Stacks", fallback="Woodblock")
            == "Woodblock-Stacks"
        )

    def test_none_uses_fallback(self):
        assert resolve_model_variant(None, fallback="Woodblock") == "Woodblock"


class TestParseOcrSettings:
    def test_defaults_when_empty(self):
        parsed = parse_ocr_settings(None, fallback_model="Woodblock")
        assert parsed == OcrRunSettings(
            k_factor=DEFAULT_K_FACTOR,
            bbox_tolerance=DEFAULT_BBOX_TOLERANCE,
            rotate=0.0,
            model_name="Woodblock",
        )

    def test_reads_page_overrides(self):
        parsed = parse_ocr_settings(
            {
                "k_factor": 3.5,
                "bbox_tolerance": 4.0,
                "rotate": 1.5,
                "model_variant": "Ume",
            },
            fallback_model="Modern",
        )
        assert parsed.k_factor == 3.5
        assert parsed.bbox_tolerance == 4.0
        assert parsed.rotate == 1.5
        assert parsed.model_name == "Ume_Druma"


class TestApplyManualRotation:
    def test_zero_degrees_is_noop(self):
        image = np.zeros((10, 10, 3), dtype=np.uint8)
        assert apply_manual_rotation(image, 0.0) is image

    @patch("BDRC.line_detection.rotate_from_angle")
    def test_positive_clockwise_negates_for_opencv(self, rotate_mock):
        image = np.zeros((10, 10, 3), dtype=np.uint8)
        rotate_mock.return_value = image
        apply_manual_rotation(image, 2.0)
        rotate_mock.assert_called_once_with(image, -2.0)


class TestBDRCOCREngineSettings:
    def test_run_on_image_forwards_parsed_settings(self):
        from BDRC.Data import OpStatus
        from app.pdf.ocr import BDRCOCREngine

        engine = BDRCOCREngine()
        engine._ready = True
        engine._active_model_name = "Modern"

        pipeline = MagicMock()
        pipeline.run_ocr.return_value = (OpStatus.SUCCESS, (None, [], [], 0.0))
        engine._pipeline = pipeline

        with patch.object(engine, "_ensure_ocr_model") as ensure_mock:
            with patch("app.pdf.ocr.apply_manual_rotation", side_effect=lambda img, _: img):
                with patch("app.pdf.ocr._normalize_to_bgr", side_effect=lambda img: img):
                    image = np.zeros((8, 8, 3), dtype=np.uint8)
                    engine.run_on_image(
                        image,
                        page_settings={
                            "k_factor": 3.1,
                            "bbox_tolerance": 2.2,
                            "model_variant": "Woodblock",
                        },
                    )

        ensure_mock.assert_called_once_with("Woodblock")
        _, kwargs = pipeline.run_ocr.call_args
        assert kwargs["k_factor"] == 3.1
        assert kwargs["bbox_tolerance"] == 2.2

    def test_ensure_ocr_model_swaps_when_variant_changes(self):
        from app.pdf.ocr import BDRCOCREngine

        engine = BDRCOCREngine()
        engine._ready = True
        engine._pipeline = MagicMock()
        engine._active_model_name = "Modern"
        woodblock_config = MagicMock(name="woodblock_config")
        engine._model_config_cache["Woodblock"] = woodblock_config

        engine._ensure_ocr_model("Woodblock")

        engine._pipeline.update_ocr_model.assert_called_once_with(woodblock_config)
        assert engine._active_model_name == "Woodblock"

    def test_missing_model_keeps_active_model(self):
        from app.pdf.ocr import BDRCOCREngine

        engine = BDRCOCREngine()
        engine._ready = True
        engine._pipeline = MagicMock()
        engine._active_model_name = "Modern"

        engine._ensure_ocr_model("Nonexistent_Model_XYZ")

        engine._pipeline.update_ocr_model.assert_not_called()
        assert engine._active_model_name == "Modern"
