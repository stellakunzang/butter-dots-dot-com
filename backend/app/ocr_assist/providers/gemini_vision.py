"""Google Gemini implementation of the vision transcription contract."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from app.ocr_assist.contracts import VisionTranscript
from app.ocr_assist.providers.media import guess_media_type


logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-2.5-pro"

_SYSTEM_PROMPT = """You are a Tibetan-script OCR system. Transcribe the page image exactly as written. \
Do not correct spelling, do not normalize variant glyphs, do not expand abbreviations, do not interpret meaning. \
Preserve line breaks where the source breaks lines. Use Unicode Tibetan script (U+0F00–U+0FFF). \
Sanskrit transliteration (mantras, dharanis) appears in real texts and uses Unicode marks like ཾ (anusvara) and ཿ (visarga); transcribe these as written.

If portions of the page are illegible (damage, ink loss, glare), transcribe what you can read and add a brief note in the ``notes`` field describing the illegible region. \
Do not guess at illegible passages.
"""

_TRANSCRIPT_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "text": {
            "type": "string",
            "description": "The transcribed Tibetan text with source line breaks preserved.",
        },
        "notes": {
            "type": "string",
            "description": "Optional caveats about illegible regions or damage.",
        },
    },
    "required": ["text"],
}


class VisionTranscriberError(RuntimeError):
    """Malformed structured response from the Gemini vision transcriber."""


class GeminiVisionTranscriber:
    """Callable wrapper around Gemini structured JSON for page transcription."""

    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL,
        client: Any = None,
        api_key: str | None = None,
    ) -> None:
        self.model = model
        self._client = client or self._build_client(api_key)

    @staticmethod
    def _build_client(api_key: str | None) -> Any:
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError(
                "Gemini vision provider requires google-genai. "
                "Install with: pip install 'google-genai>=1.0.0'"
            ) from exc

        resolved = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        return genai.Client(api_key=resolved)

    def __call__(self, *, image_path: Path) -> VisionTranscript:
        from google.genai import types

        image_bytes = image_path.read_bytes()
        mime_type = guess_media_type(image_path)

        response = self._client.models.generate_content(
            model=self.model,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                types.Part.from_text(
                    text="Transcribe this Tibetan-script page exactly as written."
                ),
            ],
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_json_schema=_TRANSCRIPT_JSON_SCHEMA,
            ),
        )

        usage = getattr(response, "usage_metadata", None)
        if usage is not None:
            logger.info(
                "gemini vision usage: prompt=%s candidates=%s total=%s",
                getattr(usage, "prompt_token_count", "?"),
                getattr(usage, "candidates_token_count", "?"),
                getattr(usage, "total_token_count", "?"),
            )

        return _parse_transcript(response)


def _parse_transcript(response: Any) -> VisionTranscript:
    raw_text = getattr(response, "text", None)
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise VisionTranscriberError("Gemini response contained no text payload")

    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise VisionTranscriberError(f"Gemini response was not valid JSON: {exc}") from exc

    text = payload.get("text")
    if not isinstance(text, str):
        raise VisionTranscriberError(
            f"Gemini transcript JSON missing string text: {type(text).__name__}"
        )

    notes_raw = payload.get("notes")
    notes = notes_raw if isinstance(notes_raw, str) and notes_raw.strip() else None
    return VisionTranscript(text=text, notes=notes)
