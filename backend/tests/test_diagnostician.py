"""
Unit tests for the Claude-backed OCR diagnostician (T-06).

The Anthropic client is faked at construction time so these tests never make
a real API call and don't need ANTHROPIC_API_KEY. Two seams are exercised:

- ``_parse_verdict`` — given a faked Claude response, returns the right
  dataclass (or raises ``DiagnosticianError`` on a malformed response).
- ``Diagnostician.__call__`` — assembles a request with the expected shape
  (vision input, cached system prompt, cached tools, ``tool_choice=any``)
  and parses the response back into a typed verdict.

Together with the retry-loop coverage in ``test_runner.py`` these pin down
the diagnostician's behavior end-to-end without burning Claude tokens.
"""
from dataclasses import dataclass
from pathlib import Path

import pytest

from app.ocr_assist.diagnostician import (
    AccurateAsSanskrit,
    Diagnostician,
    DiagnosticianError,
    NeedsHuman,
    RetryWithSettings,
    verdict_to_dict,
)
from app.ocr_assist.quality import PageQuality


def _quality(composite: float = 0.6) -> PageQuality:
    return PageQuality(
        non_tibetan_char_ratio=0.2,
        structural_error_ratio=0.1,
        sanskrit_adjusted_error_ratio=0.1,
        line_count_sanity=1.0,
        encoding_error_count=0,
        unknown_word_ratio=0.0,
        composite_score=composite,
        breakdown={"non_tibetan_penalty": 0.05},
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
    # Two-byte PNG-ish content; the diagnostician doesn't validate the bytes,
    # only that the file exists and can be base64-encoded.
    path = tmp_path / "page.png"
    path.write_bytes(b"\x89PNG fake")
    return path


class TestParseVerdict:
    def test_retry_with_settings(self):
        client = _FakeClient(
            _FakeResponse(
                content=[
                    _FakeToolUse(
                        name="retry_with_settings",
                        input={
                            "settings_overrides": {"k_factor": 3.0},
                            "rationale": "missed lines",
                        },
                    )
                ]
            )
        )
        verdict = Diagnostician(client=client)(
            image_path=Path("/dev/null"), ocr_text="x", quality=_quality(), prior_attempts=[]
        )
        # /dev/null exists on POSIX; the open is fine — payload bytes aren't
        # parsed by the diagnostician.
        assert isinstance(verdict, RetryWithSettings)
        assert verdict.settings_overrides == {"k_factor": 3.0}
        assert verdict.rationale == "missed lines"

    def test_accurate_as_sanskrit(self, image_file):
        client = _FakeClient(
            _FakeResponse(
                content=[
                    _FakeToolUse(
                        name="accurate_as_sanskrit_accept",
                        input={"rationale": "dharani"},
                    )
                ]
            )
        )
        verdict = Diagnostician(client=client)(
            image_path=image_file, ocr_text="x", quality=_quality(), prior_attempts=[]
        )
        assert isinstance(verdict, AccurateAsSanskrit)
        assert verdict.rationale == "dharani"

    def test_needs_human(self, image_file):
        client = _FakeClient(
            _FakeResponse(
                content=[
                    _FakeToolUse(
                        name="needs_human",
                        input={"reason": "torn page"},
                    )
                ]
            )
        )
        verdict = Diagnostician(client=client)(
            image_path=image_file, ocr_text="x", quality=_quality(), prior_attempts=[]
        )
        assert isinstance(verdict, NeedsHuman)
        assert verdict.reason == "torn page"

    def test_no_tool_use_block_raises(self, image_file):
        client = _FakeClient(
            _FakeResponse(content=[_FakeTextBlock(text="I'm not using tools")])
        )
        with pytest.raises(DiagnosticianError):
            Diagnostician(client=client)(
                image_path=image_file,
                ocr_text="x",
                quality=_quality(),
                prior_attempts=[],
            )

    def test_unknown_tool_name_raises(self, image_file):
        client = _FakeClient(
            _FakeResponse(
                content=[_FakeToolUse(name="vision_transcribe", input={"text": "..."})]
            )
        )
        with pytest.raises(DiagnosticianError):
            Diagnostician(client=client)(
                image_path=image_file,
                ocr_text="x",
                quality=_quality(),
                prior_attempts=[],
            )


class TestRequestShape:
    def test_request_includes_image_system_and_tools(self, image_file):
        client = _FakeClient(
            _FakeResponse(
                content=[
                    _FakeToolUse(
                        name="needs_human", input={"reason": "test"}
                    )
                ]
            )
        )
        Diagnostician(client=client, model="claude-opus-4-7")(
            image_path=image_file,
            ocr_text="ocr text here",
            quality=_quality(0.4),
            prior_attempts=[],
        )

        assert len(client.calls) == 1
        kwargs = client.calls[0]

        # Model and tool choice match the contract.
        assert kwargs["model"] == "claude-opus-4-7"
        assert kwargs["tool_choice"] == {"type": "any"}

        # System prompt is cached.
        system = kwargs["system"]
        assert isinstance(system, list) and len(system) == 1
        assert system[0]["cache_control"] == {"type": "ephemeral"}
        assert "Tibetan" in system[0]["text"]

        # Tools spec is cached on the last entry.
        tools = kwargs["tools"]
        assert {t["name"] for t in tools} == {
            "retry_with_settings",
            "accurate_as_sanskrit_accept",
            "needs_human",
        }
        assert tools[-1]["cache_control"] == {"type": "ephemeral"}
        # Earlier tools have no cache_control (a single breakpoint covers all of them).
        assert all("cache_control" not in t for t in tools[:-1])

        # User message includes image + text.
        user_content = kwargs["messages"][0]["content"]
        assert user_content[0]["type"] == "image"
        assert user_content[0]["source"]["type"] == "base64"
        assert user_content[0]["source"]["media_type"] == "image/png"
        assert user_content[1]["type"] == "text"
        assert "ocr text here" in user_content[1]["text"]
        assert "composite_score" in user_content[1]["text"]


class TestVerdictToDict:
    def test_retry(self):
        assert verdict_to_dict(
            RetryWithSettings(settings_overrides={"k_factor": 3.0}, rationale="x")
        ) == {
            "tool": "retry_with_settings",
            "settings_overrides": {"k_factor": 3.0},
            "rationale": "x",
        }

    def test_sanskrit(self):
        assert verdict_to_dict(AccurateAsSanskrit(rationale="mantra")) == {
            "tool": "accurate_as_sanskrit_accept",
            "rationale": "mantra",
        }

    def test_needs_human(self):
        assert verdict_to_dict(NeedsHuman(reason="damaged")) == {
            "tool": "needs_human",
            "reason": "damaged",
        }
