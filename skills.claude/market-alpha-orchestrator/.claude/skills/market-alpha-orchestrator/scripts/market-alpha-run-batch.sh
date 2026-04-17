#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNNER="$SCRIPT_DIR/market-alpha-agent-runner.py"

TASK_SLUG="${1:-}"
PARALLEL="${2:-2}"

echo "WARNING: market-alpha-run-batch.sh is now a legacy fallback." >&2
echo "Use OpenClaw native sessions_spawn / /subagents as the primary market-alpha execution path." >&2

ARGS=(
  --timeout 60
  run-batch
  --parallel "$PARALLEL"
)

if [[ -n "$TASK_SLUG" ]]; then
  ARGS+=(--task-slug "$TASK_SLUG")
fi

python3 "$RUNNER" "${ARGS[@]}"
