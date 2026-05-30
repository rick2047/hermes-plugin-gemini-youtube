#!/usr/bin/env python3
"""Subprocess runner for Gemini YouTube analysis.

Reads a JSON payload from stdin, calls the official google-genai SDK, and writes
a JSON result to stdout. This file runs inside the plugin-owned uv environment,
not the Hermes application venv.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any


def _json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False)


def _api_key() -> str | None:
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def _usage_to_json(response: Any) -> dict[str, Any] | None:
    try:
        raw = response.to_json_dict()
    except Exception:
        try:
            raw = response.model_dump(mode="json", exclude_none=True)
        except Exception:
            raw = None
    if not isinstance(raw, dict):
        return None
    return raw.get("usage_metadata") or raw.get("usageMetadata")


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except Exception as exc:
        print(_json({"success": False, "error": f"Invalid JSON input: {exc}"}))
        return 0

    api_key = _api_key()
    if not api_key:
        print(_json({
            "success": False,
            "error": "Missing Gemini API key. Set GEMINI_API_KEY or GOOGLE_API_KEY in ~/.hermes/.env, then restart Hermes.",
        }))
        return 0

    youtube_url = str(payload.get("youtube_url") or "").strip()
    prompt = str(payload.get("prompt") or "").strip()
    model = str(payload.get("model") or "gemini-3.5-flash").strip()
    temperature = float(payload.get("temperature", 0.2))
    max_output_tokens = int(payload.get("max_output_tokens", 8192))

    if not youtube_url or not prompt:
        print(_json({"success": False, "error": "youtube_url and prompt are required"}))
        return 0

    try:
        from google import genai
        from google.genai import types
    except Exception as exc:
        print(_json({
            "success": False,
            "error": f"google-genai is not installed in the plugin .venv: {type(exc).__name__}: {exc}",
            "client": "plugin-owned-uv-venv/google-genai",
        }))
        return 0

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=types.Content(
                parts=[
                    types.Part(file_data=types.FileData(file_uri=youtube_url)),
                    types.Part(text=prompt),
                ]
            ),
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            ),
        )
    except Exception as exc:
        print(_json({
            "success": False,
            "error": f"Gemini API call failed: {type(exc).__name__}: {exc}",
            "model": model,
            "client": "plugin-owned-uv-venv/google-genai",
        }))
        return 0

    text = (getattr(response, "text", None) or "").strip()
    if not text:
        print(_json({
            "success": False,
            "error": "Gemini returned no text output",
            "model": model,
            "client": "plugin-owned-uv-venv/google-genai",
            "usage_metadata": _usage_to_json(response),
        }))
        return 0

    print(_json({
        "success": True,
        "model": model,
        "client": "plugin-owned-uv-venv/google-genai",
        "youtube_url": youtube_url,
        "analysis": text,
        "usage_metadata": _usage_to_json(response),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
