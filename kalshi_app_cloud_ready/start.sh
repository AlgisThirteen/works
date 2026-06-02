#!/usr/bin/env sh
set -eu

HOST="${APP_HOST:-0.0.0.0}"
PORT_TO_USE="${PORT:-${APP_PORT:-8000}}"

exec python3 -m uvicorn app.main:app --host "$HOST" --port "$PORT_TO_USE"
