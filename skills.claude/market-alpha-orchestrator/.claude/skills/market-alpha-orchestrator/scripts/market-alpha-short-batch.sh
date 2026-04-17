#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
BRIDGE="$WORKSPACE_DIR/scripts/skill_multiagent_bridge.py"

usage() {
  cat <<'EOF'
Usage:
  market-alpha-short-batch.sh [options]

Options:
  --task-slug <slug>    Task slug. Optional if an active task exists.
  --market <name>       cn | us | hk. Default: multi
  --alpha-mode <name>   hunt | lead-follow. Default: hunt
  --horizon <name>      h24-48 | d3-7 | w1-2 | w2-4 | m1-3 | m3-6 | m6-12. Default: h24-48
  --objective <text>    Objective string for notes.
  --dry-run             Print prepared agent commands without executing.
  --help                Show this message.
EOF
}

TASK_SLUG=""
MARKET="multi"
ALPHA_MODE="hunt"
HORIZON="h24-48"
OBJECTIVE="hunt pre-consensus short-term buy opportunities"
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
    --alpha-mode)
      ALPHA_MODE="${2:-}"
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
    --dry-run)
      DRY_RUN="true"
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

NOTE="alpha-hunt-${ALPHA_MODE} | market=${MARKET} | horizon=${HORIZON} | objective=${OBJECTIVE}"

declare -a AGENTS=()

if [[ "$ALPHA_MODE" == "lead-follow" ]]; then
  AGENTS=(
    "planner|task decomposition|Own the lead-follow dependency graph. Force the run to separate signal_market from execution_market and optimize for ${HORIZON} execution, not generic idea generation."
    "truth-collector|source sweep|Establish verified underlying truth for all execution candidates. Persist spot truth, timestamps, primary/secondary sources, and cross-check diffs with scripts/market-alpha-truth-stack.py before downstream analysis."
    "signal-market-mapper|source sweep|Identify the earliest market and asset that emits the strongest signal. Distinguish genuine leading information from already-crowded price action."
    "execution-market-mapper|source sweep|Map each leading signal into the most executable follow trade for the user's likely session. Prefer CN/HK follow trades when US is only the signal market."
    "universe-builder|source sweep|Expand each signal theme into a single-name execution universe first. ETFs are fallback expressions, not the default answer."
    "lead-lag-analyst|historical analysis|Measure how similar signals historically transmitted across markets and over what delay. Estimate realistic lead_lag_window and decay speed."
    "single-name-driller|analysis|Validate the top execution candidates at single-name depth: estimate revisions, product/order visibility, relative strength, and flow quality."
    "crowding-killer|quality filter|Disqualify trades that require East Asia users to manage crowded US night-session single-name exposure unless explicitly requested."
    "strategy-miner|quant verification|Translate repeatable lead-follow setups into task-local strategy candidates. Use scripts/market-alpha-strategy-pool.py and reports/strategy-lab/* outputs instead of leaving patterns only in prose."
    "quant-verifier|quant verification|Validate relative strength, transmission lag, turnover regime change, expected holding window, and factor resonance for the execution market. Use task-local scripts/market-alpha-quant-compass.py and write JSON outputs under reports/quant/."
    "synthesis-analyst|synthesis|Rank opportunities by executable alpha quality, not by how important the original US signal asset is. Prefer single-name execution opportunities; ETFs are fallback only."
    "reviewer|quality review|Reject any result that confuses signal asset with execution asset, leaves horizon/entry/exit windows vague, or skips the truth ledger. Use scripts/market-alpha-truth-stack.py write-reviewer-verdict to persist a machine-readable reviewer verdict. Every actionable name must include entry trigger, entry zone, order type, stop loss, take-profit ladder, time stop, invalidation, position sizing, and max holding period. The report must include a Bot Handoff json block that a Rust bot can parse directly. The report must also include a '## Data Freshness & Completeness' section with exact markers: 'Market data as of:', 'News data as of:', 'Options data as of:', 'Options data status:', 'Timeline span:', 'Completeness status:', 'Precision level:', 'Critical missing fields:', 'Fallback sources used:', 'Mixed freshness risk:', 'Timeline integrity:', 'Open interest status:', 'Bid-ask status:', 'Expiry-window fit:'. It must include an '## 事件驱动因子' section derived from the task-local news ledger. If no single-name passes, set single_name_status=NO_SINGLE_NAME_PASSED and explicitly allow ETF-only degradation in the reviewer verdict instead of silently defaulting to ETFs. Any research fact not mapped to thesis, trigger, risk, data gap, or event driver should be removed. If data is missing, precision must downgrade to 'DIRECTIONAL_ONLY', 'WATCHLIST', or 'NOT_EXECUTABLE'. If the setup is bearish but the name is already oversold, require a bounce-failure or fresh continuation confirmation; otherwise downgrade to 'WAIT' or 'WATCHLIST'. If the report claims quant validation, it must include a Quant Evidence section with script path, input path, output path, PNG references, and score/backtest summary. Follow references/report-example-market-alpha.md."
    "report-generator|report generation|Generate the final report with signal_market, execution_market, session_fit, lead_lag_window, entry_window, exit_window, and max_holding_period explicitly filled, and write it in Simplified Chinese by default unless the user explicitly requested another language. Read the task-local reviewer verdict before drafting. Add '## Data Freshness & Completeness' with exact markers: 'Market data as of:', 'News data as of:', 'Options data as of:', 'Options data status:', 'Timeline span:', 'Completeness status:', 'Precision level:', 'Critical missing fields:', 'Fallback sources used:', 'Mixed freshness risk:', 'Timeline integrity:', 'Open interest status:', 'Bid-ask status:', 'Expiry-window fit:'. Add '## 事件驱动因子' from task-local 'news-event-log.jsonl'. For each actionable trade, provide strategy tag, direction, entry trigger, entry zone, order type, add/reduce rules, take-profit ladder, stop loss, trailing stop or none, time stop, invalidation, slippage budget, and position sizing. Add a Bot Handoff fenced json block for direct Rust-bot consumption; if the setup is not tradable, emit NOT_EXECUTABLE with reason and missing_fields instead of bluffing. If reviewer verdict says no single name passed, explicitly mark ETF output as degraded fallback rather than core alpha. If options data is incomplete, do not emit precise strike or expiry as EXECUTABLE output. If market/technical freshness is incomplete, downgrade to 'DIRECTIONAL_ONLY' or 'WATCHLIST'. Follow references/report-example-market-alpha.md. If quant validation exists, add a Quant Evidence section listing script path, input path, output path, method used, concise score/backtest summary, and markdown image references to reports/quant/*.png. Before delivery, the draft must pass 'python3 ./scripts/finance-intel-report-gate.py --report <draft-report> --task-slug ${TASK_SLUG:-<task-slug>}'. After delivery, the final user-facing handoff must include both FILEPATH and TASK_PATH so the task directory can be reopened locally. If the user explicitly asks for the whole task bundle, run market-alpha-package-task.py and include the package path plus Feishu send payload."
  )
else
  AGENTS=(
    "planner|task decomposition|Own the alpha-hunt dependency graph. Force the run to prioritize pre-consensus single-name opportunities over theme-only ETF summaries, and respect horizon ${HORIZON} instead of collapsing every task into a same-day chase."
    "truth-collector|source sweep|Establish verified underlying truth for each candidate with as_of timestamps, primary/secondary sources, and cross-check diffs. Persist truth into task-local reviewer inputs via scripts/market-alpha-truth-stack.py."
    "universe-builder|source sweep|Expand every macro/theme idea into a single-name universe first. For each theme produce long candidates, short candidates, and ETF fallback; do not stop at sector ETF summaries."
    "catalyst-hunter|source sweep|Find hidden or under-covered catalysts that can reprice a name within the active horizon ${HORIZON}. Prefer supply-chain, order-flow, policy-edge, product-cycle, or expectation-gap evidence."
    "microstructure-hunter|source sweep|Use daily and, when appropriate, minute structure to find quiet accumulation, abnormal turnover pulses, and relative strength during weak tape."
    "crowding-killer|quality filter|Actively disqualify crowded event trades, over-covered narratives, and likely exit-liquidity setups. If a setup is late, label it crowded-event or volatility-only."
    "history-analog|historical analysis|Compare with prior stealth accumulation and failed blow-off setups. Separate pre-launch structures from terminal euphoric structures."
    "single-name-driller|analysis|For top single-name candidates, validate idiosyncratic edge: product cycle, order visibility, estimate revisions, relative strength, and flow quality. ETFs should never outrank a strong single-name without explicit reviewer degradation."
    "strategy-miner|quant verification|Translate repeatable setups into task-local strategy candidates. Use scripts/market-alpha-strategy-pool.py and reports/strategy-lab/* outputs rather than leaving patterns only in prose."
    "quant-verifier|quant verification|Score anomaly strength, relative strength, turnover regime change, flow confirmation, factor resonance, and basic factor-mining evidence with lightweight numeric validation. Use task-local scripts/market-alpha-quant-compass.py and write JSON outputs under reports/quant/."
    "synthesis-analyst|synthesis|Integrate only names that survive truth, catalyst, crowding, and single-name drill-down filters. Rank single-name alpha first; ETFs are fallback expressions, not default winners."
    "reviewer|quality review|Check that the output still represents buy opportunities with asymmetry and verified spot truth. Use scripts/market-alpha-truth-stack.py write-reviewer-verdict to persist a machine-readable reviewer verdict. Reject any report that mainly explains obvious public sell-the-news setups, skips truth ledger evidence, or defaults to ETF-only output without single_name_status=NO_SINGLE_NAME_PASSED. Every actionable name must include entry trigger, entry zone, order type, stop loss, take-profit ladder, time stop, invalidation, position sizing, and max holding period. The report must include a Bot Handoff json block that a Rust bot can parse directly. The report must also include a '## Data Freshness & Completeness' section with exact markers: 'Market data as of:', 'News data as of:', 'Options data as of:', 'Options data status:', 'Timeline span:', 'Completeness status:', 'Precision level:', 'Critical missing fields:', 'Fallback sources used:'. Any research fact not mapped to thesis, trigger, risk, or data gap should be removed. If data is missing, precision must downgrade to 'DIRECTIONAL_ONLY', 'WATCHLIST', or 'NOT_EXECUTABLE'. If the report claims quant validation, it must include a Quant Evidence section with script path, input path, output path, PNG references, and score/backtest summary. Follow references/report-example-market-alpha.md."
    "report-generator|report generation|Generate the final report, explicitly tag each name as pre-consensus-buy, mispriced-catalyst, relative-strength-breakout, crowded-event, or volatility-only, then hand off for delivery. Read the task-local reviewer verdict before drafting and prefer single-name outputs over ETF wrappers. Add '## Data Freshness & Completeness' with exact markers: 'Market data as of:', 'News data as of:', 'Options data as of:', 'Options data status:', 'Timeline span:', 'Completeness status:', 'Precision level:', 'Critical missing fields:', 'Fallback sources used:'. For each actionable trade, provide strategy tag, direction, entry trigger, entry zone, order type, add/reduce rules, take-profit ladder, stop loss, trailing stop or none, time stop, invalidation, slippage budget, and position sizing. Add a Bot Handoff fenced json block for direct Rust-bot consumption; if the setup is not tradable, emit NOT_EXECUTABLE with reason and missing_fields instead of bluffing. If reviewer verdict says no single name passed, explicitly mark ETF output as degraded fallback. If options data is incomplete, do not emit precise strike or expiry as EXECUTABLE output. If market/technical freshness is incomplete, downgrade to 'DIRECTIONAL_ONLY' or 'WATCHLIST'. Map every search result to thesis, trigger, risk, or data gap; do not dump orphan research. Follow references/report-example-market-alpha.md. If quant validation exists, add a Quant Evidence section listing script path, input path, output path, method used, concise score/backtest summary, and markdown image references to reports/quant/*.png. Before delivery, the draft must pass 'python3 ./scripts/finance-intel-report-gate.py --report <draft-report> --task-slug ${TASK_SLUG:-<task-slug>}'. After delivery, the final user-facing handoff must include both FILEPATH and TASK_PATH so the task directory can be reopened locally. If the user explicitly asks for the whole task bundle, run market-alpha-package-task.py and include the package path plus Feishu send payload."
  )
fi

echo "MARKET_ALPHA_SHORT_BATCH"
echo "TASK_SLUG=${TASK_SLUG:-<active-task>}"
echo "MARKET=$MARKET"
echo "ALPHA_MODE=$ALPHA_MODE"
echo "HORIZON=$HORIZON"
echo "OBJECTIVE=$OBJECTIVE"

for spec in "${AGENTS[@]}"; do
  IFS='|' read -r AGENT_NAME ROLE MISSION <<<"$spec"
  AGENT_SLUG="$(printf '%s' "$AGENT_NAME" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//')"
  CMD=(
    python3 "$BRIDGE" prepare-agent
    --skill deep-research
  )
  if [[ -n "$TASK_SLUG" ]]; then
    CMD+=(--task-slug "$TASK_SLUG")
  fi
  CMD+=(
    --agent-name "$AGENT_NAME"
    --role "$ROLE"
    --mission "$MISSION"
    --output-path "research/${AGENT_SLUG}.md"
    --output-path "research/${AGENT_SLUG}.worklog.md"
    --output-path "research/${AGENT_SLUG}.raw.json"
    --parallel-group short-hunt
    --note "$NOTE"
  )
  printf 'COMMAND='
  printf '%q ' "${CMD[@]}"
  printf '\n'
  if [[ "$DRY_RUN" != "true" ]]; then
    "${CMD[@]}"
  fi
done
