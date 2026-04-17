#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"

TASK_SLUG="short-alpha-general-smoke"

bash "$SCRIPT_DIR/short-alpha-general-bootstrap.sh" \
  --task-slug "$TASK_SLUG" \
  --market us \
  --horizon w1-4 \
  --objective "short-alpha-general smoke" >/dev/null

TASK_DIR="$(find "$WORKSPACE_DIR/tasks" -maxdepth 1 -mindepth 1 -type d -name "*-${TASK_SLUG}" | sort | tail -n 1)"
if [[ -z "$TASK_DIR" ]]; then
  echo "Failed to resolve smoke task dir" >&2
  exit 1
fi

cp "$SKILL_DIR/fixtures/sample-market-snapshot.json" "$TASK_DIR/sources/live-market-snapshot.json"
cp "$SKILL_DIR/fixtures/sample-events.jsonl" "$TASK_DIR/sources/news-event-log.jsonl"
cp "$SKILL_DIR/fixtures/sample-candidates.json" "$TASK_DIR/sources/candidates.json"
cp "$SKILL_DIR/fixtures/sample-candidates.json" "$TASK_DIR/results/candidates/candidates.json"
mkdir -p "$TASK_DIR/reports/derivatives"
cp "$SKILL_DIR/fixtures/sample-truth-ledger.json" "$TASK_DIR/reports/derivatives/underlying-truth-ledger.json"

python3 "$TASK_DIR/scripts/short-alpha-market-observe.py" --task-slug "$TASK_SLUG" >/dev/null
python3 "$TASK_DIR/scripts/short-alpha-runtime-guard.py" status --task-slug "$TASK_SLUG" >/dev/null
python3 "$TASK_DIR/scripts/short-alpha-regime-engine.py" --task-slug "$TASK_SLUG" >/dev/null
python3 "$TASK_DIR/scripts/short-alpha-event-clock.py" --task-slug "$TASK_SLUG" >/dev/null
python3 "$TASK_DIR/scripts/short-alpha-terrain-engine.py" --task-slug "$TASK_SLUG" --candidates-input "$TASK_DIR/results/candidates/candidates-enriched.json" >/dev/null
python3 "$TASK_DIR/scripts/short-alpha-fertility-engine.py" --task-slug "$TASK_SLUG" --candidates-input "$TASK_DIR/results/candidates/candidates-enriched.json" --terrain-input "$TASK_DIR/results/terrain/terrain-map.json" --event-clock-input "$TASK_DIR/results/event-clock/trigger-watchlist.json" >/dev/null
python3 "$TASK_DIR/scripts/short-alpha-campaign-score.py" --task-slug "$TASK_SLUG" --candidates-input "$TASK_DIR/results/candidates/candidates-enriched.json" --regime-input "$TASK_DIR/results/regime/regime-snapshot.json" --terrain-input "$TASK_DIR/results/terrain/terrain-map.json" --fertility-input "$TASK_DIR/results/terrain/fertility-map.json" --event-clock-input "$TASK_DIR/results/event-clock/trigger-watchlist.json" >/dev/null
python3 "$TASK_DIR/scripts/short-alpha-execution-governor.py" --task-slug "$TASK_SLUG" --campaign-input "$TASK_DIR/results/campaign/campaign-score.json" >/dev/null
python3 "$TASK_DIR/scripts/short-alpha-capacity-pool.py" --task-slug "$TASK_SLUG" --campaign-input "$TASK_DIR/results/campaign/campaign-score.json" --execution-input "$TASK_DIR/results/execution/setup-quality.json" >/dev/null
python3 "$TASK_DIR/scripts/short-alpha-review-gate.py" --task-slug "$TASK_SLUG" --regime-input "$TASK_DIR/results/regime/regime-snapshot.json" --campaign-input "$TASK_DIR/results/campaign/campaign-score.json" --execution-input "$TASK_DIR/results/execution/setup-quality.json" >/dev/null
python3 "$TASK_DIR/scripts/short-alpha-ooda-loop.py" --task-slug "$TASK_SLUG" --regime-input "$TASK_DIR/results/regime/regime-snapshot.json" --event-clock-input "$TASK_DIR/results/event-clock/catalyst-timeline.json" --fertility-input "$TASK_DIR/results/terrain/fertility-map.json" --execution-input "$TASK_DIR/results/execution/setup-quality.json" --review-input "$TASK_DIR/reports/review/reviewer-verdict.json" >/dev/null
python3 "$TASK_DIR/scripts/short-alpha-strategy-register.py" --task-slug "$TASK_SLUG" --campaign-input "$TASK_DIR/results/campaign/campaign-score.json" --execution-input "$TASK_DIR/results/execution/setup-quality.json" --review-input "$TASK_DIR/reports/review/reviewer-verdict.json" >/dev/null
python3 "$TASK_DIR/scripts/short-alpha-score-calibration.py" --task-slug "$TASK_SLUG" --campaign-input "$TASK_DIR/results/campaign/campaign-score.json" --execution-input "$TASK_DIR/results/execution/setup-quality.json" >/dev/null
python3 "$TASK_DIR/scripts/short-alpha-report-packager.py" --task-slug "$TASK_SLUG" >/dev/null

echo "SHORT_ALPHA_GENERAL_SMOKE_OK"
echo "TASK_DIR=$TASK_DIR"
echo "REPORT=$TASK_DIR/reports/short-alpha-general/command-brief.md"
