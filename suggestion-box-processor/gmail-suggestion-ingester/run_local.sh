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
export APP_ENV=dev
export PYTHONPATH="$PROJECT_ROOT"
echo PYTHONPATH="$PYTHONPATH"
exec  python3 -m uvicorn app.main:app --reload
