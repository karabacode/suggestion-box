#!/usr/bin/env bash
set -euo pipefail

AGENT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$AGENT_ROOT/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ -f "$PROJECT_ROOT/.env" ]]; then
	set -a
	source "$PROJECT_ROOT/.env"
	set +a
fi
if [[ -f "$AGENT_ROOT/.env" ]]; then
	set -a
	source "$AGENT_ROOT/.env"
	set +a
fi

if [[ -f "$AGENT_ROOT/.venv/bin/activate" ]]; then
	source "$AGENT_ROOT/.venv/bin/activate"
elif [[ -f "$PROJECT_ROOT/suggestions-ingester/.venv/bin/activate" ]]; then
	source "$PROJECT_ROOT/suggestions-ingester/.venv/bin/activate"
elif [[ -f "$PROJECT_ROOT/.venv/bin/activate" ]]; then
	source "$PROJECT_ROOT/.venv/bin/activate"
else
	printf 'Missing virtual environment. Install requirements.txt from the project root first.\n' >&2
	exit 1
fi

export MODEL_PROVIDER="${MODEL_PROVIDER:-gemini}"
export MODEL_NAME="${MODEL_NAME:-gemini-3.6-flash}"
export TEMPERATURE="${TEMPERATURE:-0.1}"
if [[ -z "${MODEL_API_KEY:-}" ]]; then
	if [[ ! -f "$AGENT_ROOT/resources/model-api-key.txt" ]]; then
		printf 'Missing model secret. Set MODEL_API_KEY or create suggestion-agent/resources/model-api-key.txt.\n' >&2
		exit 1
	fi
	export MODEL_API_KEY="$(<"$AGENT_ROOT/resources/model-api-key.txt")"
fi
if [[ -z "$MODEL_API_KEY" ]]; then
	printf 'Model secret file is empty: %s\n' "$AGENT_ROOT/resources/model-api-key.txt" >&2
	exit 1
fi

if [[ -z "$MODEL_API_KEY" ]]; then
	printf 'Missing MODEL_API_KEY. Set it in .env or the environment.\n' >&2
	exit 1
fi

export PYTHONPATH="$PROJECT_ROOT:$AGENT_ROOT${PYTHONPATH:+:$PYTHONPATH}"

exec python3 -m uvicorn main:app --host 0.0.0.0 --port 8090 --reload
