#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TASK_BOOTSTRAP="$WORKSPACE_DIR/scripts/task-bootstrap.sh"
TASK_ORCHESTRATION="$WORKSPACE_DIR/scripts/task_orchestration.py"
SELF_SCRIPT_DIR="$SCRIPT_DIR"

usage() {
  cat <<'EOF'
Usage:
  short-alpha-general-bootstrap.sh [options]

Options:
  --task-slug <slug>       Optional task slug
  --market <name>          Default: us
  --horizon <name>         Default: w1-4
  --objective <text>       Objective summary
  --style <name>           Default: long-short
  --dry-run                Print the resolved commands without executing
  --help                   Show help
EOF
}

TASK_SLUG=""
MARKET="us"
HORIZON="w1-4"
OBJECTIVE="build a short-horizon battle plan"
STYLE="long-short"
DRY_RUN="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --task-slug)
      TASK_SLUG="${2:-}"
      shift 2
      ;;
    --market)
      MARKET="${2:-}"
      shift 2
      ;;
    --horizon)
      HORIZON="${2:-}"
      shift 2
      ;;
    --objective)
      OBJECTIVE="${2:-}"
      shift 2
      ;;
    --style)
      STYLE="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN="true"
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "$TASK_SLUG" ]]; then
  TASK_SLUG="short-alpha-general-${MARKET}-${HORIZON}"
fi

TASK_BOOTSTRAP_CMD=(
  bash "$TASK_BOOTSTRAP"
  "$TASK_SLUG"
  "short-alpha-general"
  "short-alpha-general-task"
)

echo "SHORT_ALPHA_GENERAL_BOOTSTRAP"
echo "TASK_SLUG=$TASK_SLUG"
echo "MARKET=$MARKET"
echo "HORIZON=$HORIZON"
echo "STYLE=$STYLE"
echo "OBJECTIVE=$OBJECTIVE"
printf 'BOOTSTRAP_CMD='
printf '%q ' "${TASK_BOOTSTRAP_CMD[@]}"
printf '\n'

if [[ "$DRY_RUN" == "true" ]]; then
  exit 0
fi

"${TASK_BOOTSTRAP_CMD[@]}"

TASK_DIR="$(find "$WORKSPACE_DIR/tasks" -maxdepth 1 -mindepth 1 -type d -name "*-${TASK_SLUG}" | sort | tail -n 1)"
if [[ -z "$TASK_DIR" ]]; then
  echo "Failed to resolve task directory for $TASK_SLUG" >&2
  exit 1
fi

python3 "$TASK_ORCHESTRATION" bootstrap \
  --task-slug "$TASK_SLUG" \
  --primary-skill "short-alpha-general" \
  --active-skill "short-alpha-general" \
  --reason "short-alpha-general-task" \
  --mode "battle-planning" \
  --phase "observe"

mkdir -p \
  "$TASK_DIR/results/regime" \
  "$TASK_DIR/results/event-clock" \
  "$TASK_DIR/results/terrain" \
  "$TASK_DIR/results/execution" \
  "$TASK_DIR/results/campaign" \
  "$TASK_DIR/results/candidates" \
  "$TASK_DIR/results/ooda" \
  "$TASK_DIR/results/runtime" \
  "$TASK_DIR/reports/short-alpha-general" \
  "$TASK_DIR/reports/review" \
  "$TASK_DIR/sources" \
  "$TASK_DIR/debug"

for source in "$SELF_SCRIPT_DIR"/*.py "$SELF_SCRIPT_DIR"/*.sh; do
  [ -f "$source" ] || continue
  cp "$source" "$TASK_DIR/scripts/$(basename "$source")"
  chmod +x "$TASK_DIR/scripts/$(basename "$source")" || true
done

python3 "$TASK_DIR/scripts/short-alpha-runtime-guard.py" init --task-slug "$TASK_SLUG" >/dev/null

cat > "$TASK_DIR/reports/short-alpha-general/README.md" <<EOF
# Short Alpha General Outputs

- market: $MARKET
- horizon: $HORIZON
- style: $STYLE
- objective: $OBJECTIVE

## Expected Artifacts

- results/regime/regime-snapshot.json
- results/candidates/candidates-enriched.json
- results/event-clock/catalyst-timeline.json
- results/terrain/terrain-map.json
- results/execution/setup-quality.json
- results/campaign/campaign-score.json
- results/ooda/ooda-loop.json
- results/runtime/concurrency-policy.json
- reports/short-alpha-general/strategy-registration.json
- reports/short-alpha-general/score-calibration.json
- reports/short-alpha-general/command-brief.md
- reports/review/reviewer-verdict.json

## Search Runtime Contract

- Must read and obey: \`$WORKSPACE_DIR/SEARCH_RUNTIME.md\`
- Finance/macro/market search order:
  - \`finance-mcp -> open-websearch -> zhipu -> metaso -> tavily -> brave\`
- Generic web/current market intelligence:
  - first executable search step should be \`open-websearch\`
- Do not start with Brave-backed native \`web_search\`
- \`brave\` is escalation only, not default
EOF

echo "TASK_DIR=$TASK_DIR"
echo "READY=1"
