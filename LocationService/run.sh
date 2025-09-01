#!/usr/bin/env bash
set -euo pipefail
export PYTHONUNBUFFERED=1
PORT="${PORT:-8107}"
HOST="${HOST:-0.0.0.0}"
# __main__.py reads PORT env var
exec env PORT="${PORT}" python -m app
