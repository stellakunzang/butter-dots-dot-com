"""Anthropic Claude implementation of the vision transcription contract."""
from __future__ import annotations

import logging
import os
from typing import Any

from pathlib import Path

from app.ocr_assist.contracts import VisionTranscript
from app.ocr_assist.providers.anthropic_common import (
    anthropic_image_block,
    anthropic_tools_with_cache,
    log_anthropic_usage,
)


logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-opus-4-8"
DEFAULT_MAX_TOKENS = 8192

_SYSTEM_PROMPT = """You are a Tibetan-script OCR system. Transcribe the page image exactly as written. \
Do not correct spelling, do not normalize variant glyphs, do not expand abbreviations, do not interpret meaning. \
Preserve line breaks where the source breaks lines. Use Unicode Tibetan script (U+0F00–U+0FFF). \
Sanskrit transliteration (mantras, dharanis) appears in real texts and uses Unicode marks like ཾ (anusvara) and ཿ (visarga); transcribe these as written.

If portions of the page are illegible (damage, ink loss, glare), transcribe what you can read and add a brief note in the ``notes`` field describing the illegible region. \
Do not guess at illegible passages. Return the result via the provided ``transcribe`` tool.
"""

_TOOLS = [
    {
        "name": "transcribe",
        "description": (
            "Return the exact Tibetan-script transcription of the page image. "
            "Use this for every response; never reply with free-form text."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": (
                        "The transcribed Tibetan text. Preserve line breaks from "
                        "the source. Do not add commentary or annotations inside this field."
                    ),
                },
                "notes": {
                    "type": "string",
                    "description": (
                        "Optional. Describe illegible regions, damage, mixed scripts, "
                        "or other caveats about the transcription. Omit if there are none."
                    ),
                },
            },
            "required": ["text"],
            "additionalProperties": False,
        },
    },
]


class VisionTranscriberError(RuntimeError):
    """Malformed structured response from the Anthropic vision transcriber."""


class AnthropicVisionTranscriber:
    """Callable wrapper around Claude tool use for page-image transcription."""

    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        client: Any = None,
        api_key: str | None = None,
    ) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self._client = client or self._build_client(api_key)

    @staticmethod
    def _build_client(api_key: str | None) -> Any:
        import anthropic

        return anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )

    def __call__(self, *, image_path: Path) -> VisionTranscript:
        user_content: list[dict[str, Any]] = [
            anthropic_image_block(image_path),
            {
                "type": "text",
                "text": "Transcribe this page via the `transcribe` tool.",
            },
        ]

        response = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=anthropic_tools_with_cache(_TOOLS),
            tool_choice={"type": "tool", "name": "transcribe"},
            messages=[{"role": "user", "content": user_content}],
        )

        log_anthropic_usage(logger, getattr(response, "usage", None), label="vision_ocr")
        return _parse_transcript(response)


def _parse_transcript(response: Any) -> VisionTranscript:
    tool_block = next(
        (block for block in response.content if getattr(block, "type", None) == "tool_use"),
        None,
    )
    if tool_block is None:
        raise VisionTranscriberError(
            "Claude response contained no tool_use block; "
            f"stop_reason={getattr(response, 'stop_reason', '?')}"
        )
    if tool_block.name != "transcribe":
        raise VisionTranscriberError(
            f"Unexpected tool name in vision response: {tool_block.name!r}"
        )

    inputs = tool_block.input or {}
    text = inputs.get("text")
    if not isinstance(text, str):
        raise VisionTranscriberError(
            f"transcribe tool returned non-string text: {type(text).__name__}"
        )
    notes_raw = inputs.get("notes")
    notes = notes_raw if isinstance(notes_raw, str) and notes_raw.strip() else None
    return VisionTranscript(text=text, notes=notes)
