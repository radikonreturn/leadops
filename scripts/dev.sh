#!/usr/bin/env bash

set -euo pipefail

if [[ ! -x "apps/api/.venv/bin/uvicorn" ]]; then
  echo "API virtual environment is missing. Run the API setup in README.md first."
  exit 1
fi

cleanup() {
  kill "$api_pid" "$web_pid" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

(cd apps/api && .venv/bin/uvicorn app.main:app --reload) &
api_pid=$!

(cd apps/web && npm run dev) &
web_pid=$!

wait -n "$api_pid" "$web_pid"
