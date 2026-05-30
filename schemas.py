"""Tool schemas for the Gemini YouTube analyzer plugin."""

GEMINI_YOUTUBE_ANALYZE_SCHEMA = {
    "name": "gemini_youtube_analyze",
    "description": (
        "Analyze a public YouTube video by sending the YouTube URL directly to "
        "Google Gemini's native video understanding API. Use this when the user "
        "asks to summarize, inspect, timestamp, or extract structured notes from "
        "a YouTube video without downloading it locally."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "youtube_url": {
                "type": "string",
                "description": "Public YouTube URL to analyze, e.g. https://www.youtube.com/watch?v=...",
            },
            "prompt": {
                "type": "string",
                "description": (
                    "Analysis instructions for Gemini. Ask for the exact output needed, "
                    "including timestamps, summaries, entities, matches/results, quotes, etc."
                ),
            },
            "start_time": {
                "type": "string",
                "description": (
                    "Optional timestamp/range start to focus on, e.g. '00:10:00'. "
                    "This is passed as an instruction to Gemini; the plugin still sends the public URL."
                ),
            },
            "end_time": {
                "type": "string",
                "description": (
                    "Optional timestamp/range end to focus on, e.g. '00:20:00'. "
                    "This is passed as an instruction to Gemini; the plugin still sends the public URL."
                ),
            },
            "output_style": {
                "type": "string",
                "enum": ["markdown", "json", "wiki", "timeline", "qa", "raw"],
                "description": "Optional desired output style. Defaults to markdown.",
            },
            "model": {
                "type": "string",
                "description": "Optional Gemini model name. Defaults to GEMINI_YOUTUBE_MODEL or gemini-3.5-flash.",
            },
            "temperature": {
                "type": "number",
                "description": "Optional generation temperature. Defaults to 0.2.",
            },
            "max_output_tokens": {
                "type": "integer",
                "description": "Optional max output tokens. Defaults to 8192.",
            },
            "timeout_seconds": {
                "type": "integer",
                "description": "Optional subprocess timeout in seconds. Defaults to 300.",
            },
        },
        "required": ["youtube_url", "prompt"],
    },
}
