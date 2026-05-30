"""Hermes plugin entrypoint for Gemini-native YouTube analysis."""

from __future__ import annotations

from .schemas import GEMINI_YOUTUBE_ANALYZE_SCHEMA
from .tools import check_requirements, gemini_youtube_analyze


def register(ctx) -> None:
    """Register the Gemini YouTube analyzer tool.

    The tool is gated on GEMINI_API_KEY or GOOGLE_API_KEY. With no key, the
    plugin can still be enabled/discovered, but the model will not be offered
    the tool until Hermes is restarted with a key in the environment.
    """
    ctx.register_tool(
        name="gemini_youtube_analyze",
        toolset="gemini_youtube",
        schema=GEMINI_YOUTUBE_ANALYZE_SCHEMA,
        handler=gemini_youtube_analyze,
        check_fn=check_requirements,
        description="Analyze public YouTube videos via Gemini without local downloads.",
        emoji="🎬",
    )
