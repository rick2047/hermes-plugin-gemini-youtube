"""Hermes-side wrapper for the Gemini-native YouTube analyzer.

The Hermes process itself intentionally uses only Python stdlib here. The
Google SDK lives in this plugin's own uv-managed virtualenv and is invoked via a
small subprocess runner, keeping plugin dependencies isolated from Hermes'
application venv and update workflow.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

_DEFAULT_MODEL = "gemini-3.5-flash"
_DEFAULT_TEMPERATURE = 0.2
_DEFAULT_MAX_OUTPUT_TOKENS = 8192
_DEFAULT_TIMEOUT_SECONDS = 300
_PLUGIN_DIR = Path(__file__).resolve().parent
_RUNNER = _PLUGIN_DIR / "scripts" / "analyze_youtube.py"
_VENV_PYTHON = _PLUGIN_DIR / ".venv" / "bin" / "python"
_YOUTUBE_RE = re.compile(
    r"^https?://(?:www\.|m\.)?(?:youtube\.com/(?:watch\?v=|live/|shorts/)|youtu\.be/)[A-Za-z0-9_-]",
    re.IGNORECASE,
)


def _json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False)


def _api_key() -> str | None:
    # Accept both names; Gemini provider docs commonly use either.
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def _runner_ready() -> bool:
    return _VENV_PYTHON.exists() and _RUNNER.exists()


def check_requirements() -> bool:
    """Hide the tool until a key exists and the plugin-owned runner is present."""
    return bool(_api_key()) and _runner_ready()


def _clean_model(model: Any) -> str:
    value = str(model or os.getenv("GEMINI_YOUTUBE_MODEL") or _DEFAULT_MODEL).strip()
    if value.startswith("models/"):
        value = value.split("/", 1)[1]
    return value or _DEFAULT_MODEL


def _coerce_float(raw: Any, default: float, minimum: float, maximum: float) -> float:
    try:
        value = float(raw)
    except Exception:
        return default
    return max(minimum, min(maximum, value))


def _coerce_int(raw: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(raw)
    except Exception:
        return default
    return max(minimum, min(maximum, value))


def _build_prompt(args: dict[str, Any]) -> str:
    prompt = str(args.get("prompt") or "").strip()
    start_time = str(args.get("start_time") or "").strip()
    end_time = str(args.get("end_time") or "").strip()
    output_style = str(args.get("output_style") or "markdown").strip().lower()

    extra: list[str] = []
    if start_time or end_time:
        if start_time and end_time:
            extra.append(f"Focus on the section from {start_time} to {end_time}.")
        elif start_time:
            extra.append(f"Focus from {start_time} onward.")
        else:
            extra.append(f"Focus up to {end_time}.")
    if output_style and output_style != "raw":
        extra.append(f"Return the answer in {output_style} style.")
    extra.append("When you mention events, include timestamps whenever possible.")
    extra.append("If you are uncertain about a person, quote, or result, label it as uncertain instead of guessing.")

    return prompt + ("\n\nAdditional instructions:\n- " + "\n- ".join(extra) if extra else "")


def gemini_youtube_analyze(args: dict[str, Any], **kwargs: Any) -> str:
    """Analyze a public YouTube URL using Gemini native video input.

    Hermes tool handlers receive the model-provided args dict and must return a
    JSON string. The Google SDK runs in this plugin's isolated .venv subprocess.
    """
    youtube_url = str(args.get("youtube_url") or args.get("url") or "").strip()
    prompt = str(args.get("prompt") or "").strip()

    if not youtube_url:
        return _json({"success": False, "error": "youtube_url is required"})
    if not _YOUTUBE_RE.match(youtube_url):
        return _json({
            "success": False,
            "error": "youtube_url must be a public YouTube URL from youtube.com or youtu.be",
        })
    if not prompt:
        return _json({"success": False, "error": "prompt is required"})

    if not _api_key():
        return _json({
            "success": False,
            "error": "Missing Gemini API key. Set GEMINI_API_KEY or GOOGLE_API_KEY in ~/.hermes/.env, then restart Hermes.",
        })
    if not _runner_ready():
        return _json({
            "success": False,
            "error": (
                "Gemini YouTube plugin environment is not set up. Run: "
                "cd ~/.hermes/plugins/gemini_youtube_analyzer && uv venv && uv pip install -r requirements.txt"
            ),
        })

    model = _clean_model(args.get("model"))
    temperature = _coerce_float(args.get("temperature"), _DEFAULT_TEMPERATURE, 0.0, 2.0)
    max_output_tokens = _coerce_int(
        args.get("max_output_tokens"),
        _DEFAULT_MAX_OUTPUT_TOKENS,
        128,
        65536,
    )
    timeout_seconds = _coerce_int(
        args.get("timeout_seconds"),
        _DEFAULT_TIMEOUT_SECONDS,
        30,
        1800,
    )

    payload = {
        "youtube_url": youtube_url,
        "prompt": _build_prompt(args),
        "model": model,
        "temperature": temperature,
        "max_output_tokens": max_output_tokens,
    }

    try:
        proc = subprocess.run(
            [str(_VENV_PYTHON), str(_RUNNER)],
            input=json.dumps(payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            cwd=str(_PLUGIN_DIR),
            env=os.environ.copy(),
        )
    except subprocess.TimeoutExpired:
        return _json({
            "success": False,
            "error": f"Gemini YouTube analysis timed out after {timeout_seconds}s",
            "model": model,
            "client": "plugin-owned-uv-venv/google-genai",
        })
    except Exception as exc:  # pragma: no cover - subprocess/runtime guard
        return _json({
            "success": False,
            "error": f"Could not run plugin-owned Gemini analyzer: {type(exc).__name__}: {exc}",
            "model": model,
            "client": "plugin-owned-uv-venv/google-genai",
        })

    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    if proc.returncode != 0:
        return _json({
            "success": False,
            "error": "Plugin-owned Gemini analyzer subprocess failed",
            "exit_code": proc.returncode,
            "stderr": stderr[-4000:],
            "model": model,
            "client": "plugin-owned-uv-venv/google-genai",
        })

    try:
        result = json.loads(stdout)
    except Exception:
        return _json({
            "success": False,
            "error": "Plugin-owned Gemini analyzer returned non-JSON output",
            "stdout": stdout[-4000:],
            "stderr": stderr[-4000:],
            "model": model,
            "client": "plugin-owned-uv-venv/google-genai",
        })

    # Normalize the wrapper metadata even if the runner changes later.
    if isinstance(result, dict):
        result.setdefault("model", model)
        result.setdefault("client", "plugin-owned-uv-venv/google-genai")
        return _json(result)

    return _json({
        "success": False,
        "error": "Plugin-owned Gemini analyzer returned an unexpected JSON shape",
        "raw_result": result,
        "model": model,
        "client": "plugin-owned-uv-venv/google-genai",
    })
