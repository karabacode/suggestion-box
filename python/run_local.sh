#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

if [[ -f "$PROJECT_ROOT/.venv/bin/activate" ]]; then
	source "$PROJECT_ROOT/.venv/bin/activate"
elif [[ -f "$PROJECT_ROOT/../.venv/bin/activate" ]]; then
	source "$PROJECT_ROOT/../.venv/bin/activate"
else
	printf 'Missing virtual environment. Create ../.venv or .venv first.\n' >&2
	exit 1
fi

if [[ -z "${MAINTENANCE_PASSWORD:-}" ]]; then
	if [[ ! -f app/resources/maintenance-password.txt ]]; then
		printf 'Missing maintenance password. Set MAINTENANCE_PASSWORD or create app/resources/maintenance-password.txt.\n' >&2
		exit 1
	fi
	export MAINTENANCE_PASSWORD="$(<app/resources/maintenance-password.txt)"
fi
if [[ -z "${GOOGLE_CLIENT_SECRET_JSON:-}" ]]; then
	if [[ ! -f app/resources/google-client-secret.json ]]; then
		printf 'Missing Google client secret. Set GOOGLE_CLIENT_SECRET_JSON or create app/resources/google-client-secret.json.\n' >&2
		exit 1
	fi
	export GOOGLE_CLIENT_SECRET_JSON="$(<app/resources/google-client-secret.json)"
fi
if [[ -z "${GMAIL_TOKEN_JSON:-}" ]]; then
	if [[ ! -f app/resources/gmail-lewis-secret.json ]]; then
		printf 'Missing Gmail token. Set GMAIL_TOKEN_JSON or create app/resources/gmail-lewis-secret.json.\n' >&2
		exit 1
	fi
	export GMAIL_TOKEN_JSON="$(<app/resources/gmail-lewis-secret.json)"
fi
export OAUTHLIB_INSECURE_TRANSPORT=1
export GOOGLE_CLOUD_PROJECT="suggestion-box-508020"
export GOOGLE_PUBSUB_TOPIC="projects/suggestion-box-508020/topics/new-email"

exec python3 -m uvicorn app.main:app --reload
