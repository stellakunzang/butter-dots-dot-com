"""Guardrails so Interactive OCR Assist cannot ship enabled in production."""
import pytest

from app.config import Settings, assert_ocr_assist_safe_to_enable, running_on_render


def test_ocr_assist_local_default_is_false():
    """CI lock: the Settings default must stay False so prod cannot inherit on."""
    assert Settings.model_fields["ocr_assist_local"].default is False


def test_running_on_render_detects_render_env(monkeypatch):
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("RENDER_SERVICE_ID", raising=False)
    assert running_on_render() is False

    monkeypatch.setenv("RENDER", "true")
    assert running_on_render() is True


def test_assert_ocr_assist_safe_allows_local_enable(monkeypatch):
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("RENDER_SERVICE_ID", raising=False)
    monkeypatch.setenv("OCR_ASSIST_LOCAL", "true")

    import importlib
    import app.config as config_mod

    importlib.reload(config_mod)
    config_mod.assert_ocr_assist_safe_to_enable()  # must not raise


def test_assert_ocr_assist_safe_blocks_render(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("OCR_ASSIST_LOCAL", "true")

    import importlib
    import app.config as config_mod

    importlib.reload(config_mod)
    with pytest.raises(RuntimeError, match="OCR_ASSIST_LOCAL"):
        config_mod.assert_ocr_assist_safe_to_enable()

    # Restore for the rest of the suite.
    monkeypatch.delenv("OCR_ASSIST_LOCAL", raising=False)
    monkeypatch.delenv("RENDER", raising=False)
    importlib.reload(config_mod)
