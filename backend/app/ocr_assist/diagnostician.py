"""
Claude-backed OCR diagnostician for the interactive workflow.

See ``docs/planning/INTERACTIVE_OCR_PLAN.md`` § T-06 for the design. The
runner calls ``Diagnostician`` when a page's quality score falls below
``accept`` and there are attempts remaining. The diagnostician sees the
page image, the OCR text, the quality breakdown, and prior attempts; it
returns one of three verdicts, all routed through Claude tool use so the
output is structurally typed (no JSON parsing of free-form text).

Verdicts in scope for T-06:

- ``RetryWithSettings`` — overrides to apply to the page's settings on the
  next OCR attempt (T-07 plugs in vision-OCR fallback as a fourth verdict).
- ``AccurateAsSanskrit`` — the OCR is faithful to Sanskrit transliteration
  in the source; stop the loop and accept the current text.
- ``NeedsHuman`` — the page is unrecoverable by the AI loop; queue for
  human review with a stated reason.

The class is callable so ``runner.run_page`` can take it as
``claude_diagnostician``; tests can substitute any callable with the same
signature without an Anthropic API key. The system prompt and tools spec
are cached (``cache_control: ephemeral``) so the second and later calls
within a job pay the much-cheaper cache-read rate — see
``shared/prompt-caching.md`` if extending this.

Deploy posture: ``behind-flag`` per the plan. This module reads
``ANTHROPIC_API_KEY`` from the environment and is gated by the runner only
calling it when a non-None diagnostician is passed; no API surface
exposes it yet.
"""
from __future__ import annotations

import base64
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Union

from app.ocr_assist.job_store import AttemptRecord
from app.ocr_assist.quality import PageQuality


logger = logging.getLogger(__name__)


DEFAULT_MODEL = "claude-opus-4-7"
DEFAULT_MAX_TOKENS = 2048

_SYSTEM_PROMPT = """You are an OCR diagnostician for Tibetan-script pages run through the BDRC OCR pipeline. \
On each turn you see one page: the image, the current OCR output, a quality breakdown, and prior attempt(s) on the same page. \
Your job is to pick the single best next action via one of the three tools provided.

The quality breakdown fields are all in [0, 1] except ``encoding_error_count`` (non-negative integer). \
Higher composite means cleaner output. Phase-1 spell-check (structural rules) is the main signal; \
Phase-2 (corpus lookup) is currently weighted 0 because the corpus is unpopulated.

Sanskrit transliteration legitimately breaks Tibetan stacking rules (mantras, dharanis, proper names). \
If most flagged syllables look Sanskrit and the OCR plausibly matches the image, prefer ``accurate_as_sanskrit_accept`` \
over recommending retries — that path stops the loop cleanly.

Settings you can override via ``retry_with_settings`` (omit any you do not want to change):
- ``k_factor`` (float, default 2.5): line-detection sensitivity; raise it (~3.0) when lines are missed or fragmented.
- ``bbox_tolerance`` (float, default 3.0): line-merge tolerance.
- ``model_variant`` (string): ``"Modern"`` (default), ``"Woodblock"``, ``"Ume"``. Choose ``Woodblock`` for printed pecha pages, ``Ume`` for cursive.
- ``rotate`` (float): page rotation in degrees, positive = clockwise. Use for skewed scans.

Choose ``needs_human`` when the image is fundamentally unreadable (heavy damage, multi-column layouts BDRC cannot handle, mixed scripts you cannot recover with a setting change). Provide a brief reason. \
Choose ``retry_with_settings`` only when you have a concrete hypothesis the override will help — vague "try again" verdicts waste budget.

You may not propose a custom transcription. That is a separate fallback that does not exist in this version.
"""


_TOOLS = [
    {
        "name": "retry_with_settings",
        "description": (
            "Retry OCR on this page with the given setting overrides. "
            "Only include fields you want to change from the page's current settings."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "settings_overrides": {
                    "type": "object",
                    "description": "Settings to merge over the page's current settings before re-running OCR.",
                    "properties": {
                        "k_factor": {"type": "number"},
                        "bbox_tolerance": {"type": "number"},
                        "model_variant": {
                            "type": "string",
                            "enum": ["Modern", "Woodblock", "Ume"],
                        },
                        "rotate": {"type": "number"},
                    },
                    "additionalProperties": False,
                },
                "rationale": {
                    "type": "string",
                    "description": "One-sentence justification for the override choice.",
                },
            },
            "required": ["settings_overrides", "rationale"],
            "additionalProperties": False,
        },
    },
    {
        "name": "accurate_as_sanskrit_accept",
        "description": (
            "Accept the current OCR text as a faithful transcription of Sanskrit "
            "transliteration in the source. Stops the retry loop cleanly."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "rationale": {
                    "type": "string",
                    "description": "Why the OCR output is accurate Sanskrit content.",
                },
            },
            "required": ["rationale"],
            "additionalProperties": False,
        },
    },
    {
        "name": "needs_human",
        "description": (
            "The page cannot be recovered by another OCR attempt — surface to a human."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Concrete reason the page needs human review.",
                },
            },
            "required": ["reason"],
            "additionalProperties": False,
        },
    },
]


@dataclass(frozen=True)
class RetryWithSettings:
    settings_overrides: dict[str, Any]
    rationale: str


@dataclass(frozen=True)
class AccurateAsSanskrit:
    rationale: str


@dataclass(frozen=True)
class NeedsHuman:
    reason: str


Verdict = Union[RetryWithSettings, AccurateAsSanskrit, NeedsHuman]


class DiagnosticianError(RuntimeError):
    """The diagnostician received a malformed Claude response.

    Distinct from ``anthropic.APIError`` (network/server/auth failures): this
    raises only when the response shape is wrong (no tool call, unknown tool
    name). Callers can choose to fall back to ``NeedsHuman`` rather than
    crashing the loop.
    """


class Diagnostician:
    """Callable wrapper around the Claude API for OCR verdicts.

    Instantiate once per job (not per page) so the SDK client and the cached
    system prompt are reused — every call after the first reads tokens from
    cache at ~10% of the input rate. ``__call__`` matches the
    ``claude_diagnostician`` argument of ``runner.run_page``.
    """

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

        return anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    def __call__(
        self,
        *,
        image_path: Path,
        ocr_text: str,
        quality: PageQuality,
        prior_attempts: list[AttemptRecord],
    ) -> Verdict:
        image_bytes = image_path.read_bytes()
        image_b64 = base64.standard_b64encode(image_bytes).decode("ascii")

        user_content: list[dict[str, Any]] = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": _guess_media_type(image_path),
                    "data": image_b64,
                },
            },
            {
                "type": "text",
                "text": _render_user_prompt(ocr_text, quality, prior_attempts),
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
            tools=_tools_with_cache(),
            tool_choice={"type": "any"},
            messages=[{"role": "user", "content": user_content}],
        )

        usage = getattr(response, "usage", None)
        if usage is not None:
            logger.info(
                "diagnostician usage: input=%s cache_read=%s cache_create=%s output=%s",
                getattr(usage, "input_tokens", "?"),
                getattr(usage, "cache_read_input_tokens", "?"),
                getattr(usage, "cache_creation_input_tokens", "?"),
                getattr(usage, "output_tokens", "?"),
            )

        return _parse_verdict(response)


def _render_user_prompt(
    ocr_text: str,
    quality: PageQuality,
    prior_attempts: list[AttemptRecord],
) -> str:
    breakdown = json.dumps(
        {
            "composite_score": quality.composite_score,
            "non_tibetan_char_ratio": quality.non_tibetan_char_ratio,
            "structural_error_ratio": quality.structural_error_ratio,
            "sanskrit_adjusted_error_ratio": quality.sanskrit_adjusted_error_ratio,
            "line_count_sanity": quality.line_count_sanity,
            "encoding_error_count": quality.encoding_error_count,
            "unknown_word_ratio": quality.unknown_word_ratio,
            "breakdown": quality.breakdown,
        },
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    )
    attempts_section = _render_prior_attempts(prior_attempts)
    return (
        "Current OCR output:\n"
        "```\n"
        f"{ocr_text}\n"
        "```\n\n"
        "Quality breakdown:\n"
        "```json\n"
        f"{breakdown}\n"
        "```\n\n"
        f"{attempts_section}"
        "Choose the best next action via one of the tools."
    )


def _render_prior_attempts(prior_attempts: list[AttemptRecord]) -> str:
    if not prior_attempts:
        return "Prior attempts: none.\n\n"
    lines = ["Prior attempts on this page (oldest first):"]
    for attempt in prior_attempts:
        composite = "?"
        if attempt.quality and "composite_score" in attempt.quality:
            composite = f"{attempt.quality['composite_score']:.3f}"
        verdict_summary = "no verdict"
        if attempt.ai_verdict:
            tool = attempt.ai_verdict.get("tool", "?")
            rationale = attempt.ai_verdict.get("rationale") or attempt.ai_verdict.get("reason", "")
            verdict_summary = f"{tool}: {rationale}"
        lines.append(
            f"- attempt {attempt.number}: composite={composite}; verdict={verdict_summary}"
        )
    lines.append("")
    return "\n".join(lines) + "\n"


def _tools_with_cache() -> list[dict[str, Any]]:
    """Tools list with ``cache_control`` on the last tool.

    The cache_control marker on the last block of the tools array caches
    the entire tools spec. We attach a fresh dict so the module-level
    constant stays clean.
    """
    tools = [dict(t) for t in _TOOLS]
    tools[-1] = {**tools[-1], "cache_control": {"type": "ephemeral"}}
    return tools


def _parse_verdict(response: Any) -> Verdict:
    tool_block = next(
        (block for block in response.content if getattr(block, "type", None) == "tool_use"),
        None,
    )
    if tool_block is None:
        raise DiagnosticianError(
            "Claude response contained no tool_use block; "
            f"stop_reason={getattr(response, 'stop_reason', '?')}"
        )

    name = tool_block.name
    inputs = tool_block.input or {}

    if name == "retry_with_settings":
        return RetryWithSettings(
            settings_overrides=dict(inputs.get("settings_overrides") or {}),
            rationale=str(inputs.get("rationale", "")),
        )
    if name == "accurate_as_sanskrit_accept":
        return AccurateAsSanskrit(rationale=str(inputs.get("rationale", "")))
    if name == "needs_human":
        return NeedsHuman(reason=str(inputs.get("reason", "")))

    raise DiagnosticianError(f"Unknown tool name in Claude response: {name!r}")


def verdict_to_dict(verdict: Verdict) -> dict[str, Any]:
    """Serialize a verdict for persistence under ``attempts/NN/ai_verdict.json``."""
    if isinstance(verdict, RetryWithSettings):
        return {
            "tool": "retry_with_settings",
            "settings_overrides": dict(verdict.settings_overrides),
            "rationale": verdict.rationale,
        }
    if isinstance(verdict, AccurateAsSanskrit):
        return {"tool": "accurate_as_sanskrit_accept", "rationale": verdict.rationale}
    if isinstance(verdict, NeedsHuman):
        return {"tool": "needs_human", "reason": verdict.reason}
    raise TypeError(f"Unknown verdict type: {type(verdict).__name__}")


def _guess_media_type(image_path: Path) -> str:
    suffix = image_path.suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }.get(suffix, "image/png")
