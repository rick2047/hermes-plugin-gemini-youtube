#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
uv venv
uv sync
.venv/bin/python - <<'PY'
from google import genai
from google.genai import types
print('google-genai ready')
PY
