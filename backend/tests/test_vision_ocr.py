"""
Unit tests for the Claude vision-OCR fallback (T-07).

The Anthropic client is faked at construction time so these tests never make
a real API call and don't need ``ANTHROPIC_API_KEY``. Two seams are
exercised:

- ``_parse_transcript`` — given a faked Claude response, returns a typed
  ``VisionTranscript`` or raises ``VisionOcrError`` on a malformed response.
- ``VisionOcr.__call__`` — assembles a request with the expected shape
  (image input, cached system prompt, cached tools, forced-tool choice)
  and parses the response back into the transcript dataclass.

Together with the runner-level fallback tests in ``test_runner.py`` these
pin down the vision module's behavior end-to-end without burning tokens.
"""
from dataclasses import dataclass
from pathlib import Path

import pytest

from app.ocr_assist.vision_ocr import (
    VisionOcr,
    VisionOcrError,
    VisionTranscript,
    transcript_to_dict,
)


@dataclass
class _FakeToolUse:
    """Minimal stand-in for ``anthropic.types.ToolUseBlock``."""
    name: str
    input: dict
    type: str = "tool_use"


@dataclass
class _FakeTextBlock:
    text: str
    type: str = "text"


@dataclass
class _FakeUsage:
    input_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class _FakeResponse:
    content: list
    usage: _FakeUsage = None
    stop_reason: str = "tool_use"

    def __post_init__(self):
        if self.usage is None:
            self.usage = _FakeUsage()


class _FakeClient:
    """Records the request kwargs and returns a canned response."""

    def __init__(self, response):
        self._response = response
        self.calls: list[dict] = []

    @property
    def messages(self):
        return self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self._response


@pytest.fixture
def image_file(tmp_path: Path) -> Path:
    path = tmp_path / "page.png"
    # The vision module doesn't validate PNG bytes — just that the file exists
    # and can be base64-encoded.
    path.write_bytes(b"\x89PNG fake")
    return path


class TestParseTranscript:
    def test_text_only(self, image_file):
        client = _FakeClient(
            _FakeResponse(
                content=[
                    _FakeToolUse(
                        name="transcribe",
                        input={"text": "བཀྲ་ཤིས་"},
                    )
                ]
            )
        )
        transcript = VisionOcr(client=client)(image_path=image_file)
        assert isinstance(transcript, VisionTranscript)
        assert transcript.text == "བཀྲ་ཤིས་"
        assert transcript.notes is None

    def test_text_and_notes(self, image_file):
        client = _FakeClient(
            _FakeResponse(
                content=[
                    _FakeToolUse(
                        name="transcribe",
                        input={
                            "text": "བཀྲ་ཤིས་",
                            "notes": "ink loss in bottom-right corner",
                        },
                    )
                ]
            )
        )
        transcript = VisionOcr(client=client)(image_path=image_file)
        assert transcript.notes == "ink loss in bottom-right corner"

    def test_blank_notes_treated_as_absent(self, image_file):
        # The schema marks ``notes`` optional but Claude may still emit an empty
        # string. Persisting an empty string would clutter the UI; drop it.
        client = _FakeClient(
            _FakeResponse(
                content=[
                    _FakeToolUse(
                        name="transcribe",
                        input={"text": "x", "notes": "   "},
                    )
                ]
            )
        )
        transcript = VisionOcr(client=client)(image_path=image_file)
        assert transcript.notes is None

    def test_no_tool_use_block_raises(self, image_file):
        client = _FakeClient(
            _FakeResponse(content=[_FakeTextBlock(text="I refuse")])
        )
        with pytest.raises(VisionOcrError):
            VisionOcr(client=client)(image_path=image_file)

    def test_wrong_tool_name_raises(self, image_file):
        client = _FakeClient(
            _FakeResponse(
                content=[_FakeToolUse(name="diagnose", input={"text": "x"})]
            )
        )
        with pytest.raises(VisionOcrError):
            VisionOcr(client=client)(image_path=image_file)

    def test_missing_text_raises(self, image_file):
        client = _FakeClient(
            _FakeResponse(
                content=[_FakeToolUse(name="transcribe", input={"notes": "x"})]
            )
        )
        with pytest.raises(VisionOcrError):
            VisionOcr(client=client)(image_path=image_file)


class TestRequestShape:
    def test_request_includes_image_system_and_tool(self, image_file):
        client = _FakeClient(
            _FakeResponse(
                content=[_FakeToolUse(name="transcribe", input={"text": "x"})]
            )
        )
        VisionOcr(client=client, model="claude-opus-4-7")(image_path=image_file)

        assert len(client.calls) == 1
        kwargs = client.calls[0]

        assert kwargs["model"] == "claude-opus-4-7"
        # Forced-tool choice: vision must always go through the transcribe tool,
        # not "any" — there's only one tool and free-form text is explicitly
        # disallowed by the prompt.
        assert kwargs["tool_choice"] == {"type": "tool", "name": "transcribe"}

        system = kwargs["system"]
        assert isinstance(system, list) and len(system) == 1
        assert system[0]["cache_control"] == {"type": "ephemeral"}
        assert "Tibetan" in system[0]["text"]
        # The strictness language is the whole point of vision-OCR; pin it.
        assert "exactly as written" in system[0]["text"]

        tools = kwargs["tools"]
        assert [t["name"] for t in tools] == ["transcribe"]
        assert tools[-1]["cache_control"] == {"type": "ephemeral"}

        user_content = kwargs["messages"][0]["content"]
        assert user_content[0]["type"] == "image"
        assert user_content[0]["source"]["type"] == "base64"
        assert user_content[0]["source"]["media_type"] == "image/png"
        assert user_content[1]["type"] == "text"

    def test_defaults_to_opus(self, image_file):
        # Vision is the costly fallback that runs at most once per failed page;
        # default to the strongest model. Callers can pass model= to override.
        client = _FakeClient(
            _FakeResponse(
                content=[_FakeToolUse(name="transcribe", input={"text": "x"})]
            )
        )
        VisionOcr(client=client)(image_path=image_file)
        assert client.calls[0]["model"] == "claude-opus-4-8"


class TestTranscriptToDict:
    def test_text_only(self):
        assert transcript_to_dict(VisionTranscript(text="བཀྲ")) == {"text": "བཀྲ"}

    def test_with_notes(self):
        assert transcript_to_dict(
            VisionTranscript(text="བཀྲ", notes="faded ink")
        ) == {"text": "བཀྲ", "notes": "faded ink"}
