#!/usr/bin/env bash
set -euo pipefail

SERVICE_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SERVICE_ROOT/.." && pwd)"
cd "$SERVICE_ROOT"

if [[ -f "$PROJECT_ROOT/.env" ]]; then
  set -a
  source "$PROJECT_ROOT/.env"
  set +a
fi

if [[ -f "$SERVICE_ROOT/.env" ]]; then
  set -a
  source "$SERVICE_ROOT/.env"
  set +a
fi

if [[ -f "$PROJECT_ROOT/suggestions-ingester/.venv/bin/activate" ]]; then
  source "$PROJECT_ROOT/suggestions-ingester/.venv/bin/activate"
else
  printf 'Missing virtual environment.\n' >&2
  exit 1
fi

if [[ -z "${GMAIL_TOKEN_JSON:-}" ]]; then
  printf 'Missing GMAIL_TOKEN_JSON. Set the send-authorized Gmail token.\n' >&2
  exit 1
fi

export PYTHONPATH="$SERVICE_ROOT:$SERVICE_ROOT/..${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8091 --reload
