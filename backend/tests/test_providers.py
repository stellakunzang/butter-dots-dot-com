"""Tests for LLM provider factories."""
from unittest.mock import MagicMock, patch

import pytest

from app.ocr_assist.contracts import VisionTranscript
from app.ocr_assist.providers import build_diagnostician, build_vision_transcriber
from app.ocr_assist.providers.anthropic_diagnostician import AnthropicDiagnostician
from app.ocr_assist.providers.anthropic_vision import AnthropicVisionTranscriber
from app.ocr_assist.providers.gemini_vision import (
    DEFAULT_MODEL as GEMINI_DEFAULT_MODEL,
    GeminiVisionTranscriber,
)


class TestBuildDiagnostician:
    def test_defaults_to_anthropic(self):
        assert isinstance(build_diagnostician(), AnthropicDiagnostician)

    def test_accepts_claude_alias(self):
        assert isinstance(build_diagnostician("claude"), AnthropicDiagnostician)

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown diagnostician provider"):
            build_diagnostician("openai")


class TestBuildVisionTranscriber:
    def test_defaults_to_anthropic(self):
        assert isinstance(build_vision_transcriber(), AnthropicVisionTranscriber)

    @patch.object(GeminiVisionTranscriber, "_build_client", return_value=MagicMock())
    def test_gemini_provider(self, _mock_client):
        assert isinstance(build_vision_transcriber("gemini"), GeminiVisionTranscriber)

    @patch.object(GeminiVisionTranscriber, "_build_client", return_value=MagicMock())
    def test_google_alias(self, _mock_client):
        assert isinstance(build_vision_transcriber("google"), GeminiVisionTranscriber)

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown vision OCR provider"):
            build_vision_transcriber("openai")


class TestGeminiVisionTranscriber:
    def test_parses_structured_json_response(self, tmp_path):
        from app.ocr_assist.providers.gemini_vision import GeminiVisionTranscriber

        image_path = tmp_path / "page.png"
        image_path.write_bytes(b"\x89PNG fake")

        class _FakeUsage:
            prompt_token_count = 100
            candidates_token_count = 50
            total_token_count = 150

        class _FakeResponse:
            text = '{"text": "བཀྲ་ཤིས་", "notes": "faded corner"}'
            usage_metadata = _FakeUsage()

        class _FakeModels:
            def generate_content(self, **kwargs):
                self.last_kwargs = kwargs
                return _FakeResponse()

        class _FakeClient:
            models = _FakeModels()

        transcriber = GeminiVisionTranscriber(client=_FakeClient())
        transcript = transcriber(image_path=image_path)

        assert isinstance(transcript, VisionTranscript)
        assert transcript.text == "བཀྲ་ཤིས་"
        assert transcript.notes == "faded corner"
        assert transcriber._client.models.last_kwargs["model"] == GEMINI_DEFAULT_MODEL
