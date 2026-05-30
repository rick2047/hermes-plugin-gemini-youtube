# Gemini YouTube Analyzer Hermes Plugin

Hermes plugin that adds `gemini_youtube_analyze`, a tool for analyzing public YouTube videos using Gemini's native video/YouTube URL support.

## What it does

- Sends the public YouTube URL directly to Gemini as `fileData.fileUri`.
- Uses Google's official `google-genai` Python SDK in this plugin's own uv-managed `.venv`, matching the docs' `types.Part(file_data=types.FileData(file_uri=...))` pattern.
- Does **not** install Google SDK packages into the Hermes application venv.
- Does **not** download video files locally.
- Returns JSON containing the model name, URL, analysis text, client type, and Gemini usage metadata when available.

## Setup

1. Create/update the plugin-owned uv environment:

   ```bash
   cd ~/.hermes/plugins/gemini_youtube_analyzer
   ./setup_env.sh
   ```

   Equivalent manual commands:

   ```bash
   uv venv
   uv sync
   ```

2. Enable the plugin:

   ```bash
   hermes plugins enable gemini_youtube_analyzer
   ```

3. Add a Gemini API key later to `~/.hermes/.env`:

   ```bash
   GEMINI_API_KEY=[REDACTED]
   ```

   `GOOGLE_API_KEY` is also accepted.

4. Restart Hermes / gateway so the environment and plugin registry reload.

## Runtime architecture

Hermes imports only stdlib wrapper code from `tools.py`. The actual Gemini SDK call runs as a subprocess:

```text
Hermes venv
  -> ~/.hermes/plugins/gemini_youtube_analyzer/.venv/bin/python
     -> scripts/analyze_youtube.py
        -> google-genai
```

This keeps plugin dependencies external to Hermes core and resilient across `hermes update`.

## Tool arguments

Required:

- `youtube_url`: public YouTube URL
- `prompt`: the analysis request

Optional:

- `start_time`, `end_time`: passed as focus instructions to Gemini
- `output_style`: `markdown`, `json`, `wiki`, `timeline`, `qa`, or `raw`
- `model`: defaults to `GEMINI_YOUTUBE_MODEL`, or `gemini-3.5-flash` if unset
- `temperature`: defaults to `0.2`
- `max_output_tokens`: defaults to `8192`
- `timeout_seconds`: subprocess timeout, defaults to `300`

## Example prompt for WXM

```text
Analyze this WXM Ground Zero episode. Return a timestamped timeline with matches/results, promos/interviews, wrestler appearances, storyline developments, notable quotes, and a wiki-ready episode summary. Mark uncertain identifications as uncertain rather than guessing.
```
