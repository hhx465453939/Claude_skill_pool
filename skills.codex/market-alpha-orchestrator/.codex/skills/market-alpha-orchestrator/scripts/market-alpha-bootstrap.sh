#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TASK_BOOTSTRAP="$WORKSPACE_DIR/scripts/task-bootstrap.sh"
DEEP_RESEARCH_BOOTSTRAP="$WORKSPACE_DIR/scripts/deep-research-bootstrap.sh"
SUPERPOWERS_BOOTSTRAP="$WORKSPACE_DIR/scripts/superpowers-bootstrap.sh"
TASK_ORCHESTRATION="$WORKSPACE_DIR/scripts/task_orchestration.py"
QUANT_SETUP="$SCRIPT_DIR/market-alpha-quant-setup.py"
DATA_LAYER_SETUP="$SCRIPT_DIR/market-alpha-data-layer.py"
NATIVE_SUBAGENTS_PREP="$SCRIPT_DIR/market-alpha-native-subagents.py"
NATIVE_COORDINATOR="$SCRIPT_DIR/market-alpha-native-coordinator.py"
SHORT_ALPHA_GENERAL_BOOTSTRAP="$WORKSPACE_DIR/skills/short-alpha-general/scripts/short-alpha-general-bootstrap.sh"

slugify() {
  local raw="${1:-}"
  local slug
  slug="$(printf '%s' "$raw" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//')"
  if [[ -z "$slug" ]]; then
    slug="market-alpha"
  fi
  printf '%s\n' "$slug"
}

usage() {
  cat <<'EOF'
Usage:
  market-alpha-bootstrap.sh [options]

Options:
  --task-slug <slug>         Task slug. Optional.
  --engine <name>            auto | hybrid | superpowers | deep-research. Default: auto
  --market <name>            cn | us | hk | futures | options | fund | crypto | multi
  --style <name>             long | short | hybrid
  --alpha-mode <name>        normal | hunt | lead-follow | crowded-event | volatility-only. Default: normal
  --horizon <name>           auto | h24-48 | d3-7 | w1-2 | w2-4 | m1-3 | m3-6 | m6-12 | y1-3 | y3-5 | y10-plus. Default: auto
  --depth <name>             scan | deep-dive | trade-plan | derivatives. Default: scan
  --instrument <name>        equity | sector | index | commodity | derivative | fund
  --objective <text>         Objective text
  --deliverable <text>       Deliverable text
  --scope <text>             Scope text
  --reason <text>            Reason text
  --preset <name>            auto | light | default | high-throughput. Default: auto
  --note <text>              Extra note
  --dry-run                  Print the resolved command without executing
  --help                     Show this message
EOF
}

TASK_SLUG=""
ENGINE="auto"
MARKET="multi"
STYLE="hybrid"
ALPHA_MODE="normal"
HORIZON="auto"
DEPTH="scan"
INSTRUMENT="equity"
OBJECTIVE=""
DELIVERABLE=""
SCOPE=""
REASON=""
PRESET="auto"
NOTE=""
DRY_RUN="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --task-slug)
      TASK_SLUG="${2:-}"
      shift 2
      ;;
    --engine)
      ENGINE="${2:-}"
      shift 2
      ;;
    --market)
      MARKET="${2:-}"
      shift 2
      ;;
    --style)
      STYLE="${2:-}"
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
    --depth)
      DEPTH="${2:-}"
      shift 2
      ;;
    --instrument)
      INSTRUMENT="${2:-}"
      shift 2
      ;;
    --objective)
      OBJECTIVE="${2:-}"
      shift 2
      ;;
    --deliverable)
      DELIVERABLE="${2:-}"
      shift 2
      ;;
    --scope)
      SCOPE="${2:-}"
      shift 2
      ;;
    --reason)
      REASON="${2:-}"
      shift 2
      ;;
    --preset)
      PRESET="${2:-}"
      shift 2
      ;;
    --note)
      NOTE="${2:-}"
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

ENGINE="$(slugify "$ENGINE")"
MARKET="$(slugify "$MARKET")"
STYLE="$(slugify "$STYLE")"
ALPHA_MODE="$(slugify "$ALPHA_MODE")"
HORIZON="$(slugify "$HORIZON")"
DEPTH="$(slugify "$DEPTH")"
INSTRUMENT="$(slugify "$INSTRUMENT")"
PRESET="$(slugify "$PRESET")"

if [[ -z "$TASK_SLUG" ]]; then
  TASK_SLUG="$(slugify "${MARKET}-${STYLE}-${INSTRUMENT}-market-alpha")"
fi

if [[ -z "$REASON" ]]; then
  REASON="market-alpha-${ENGINE}-${MARKET}-${STYLE}-${ALPHA_MODE}-${INSTRUMENT}"
fi

if [[ -z "$OBJECTIVE" ]]; then
  OBJECTIVE="Build a ${STYLE} ${MARKET} ${INSTRUMENT} ${ALPHA_MODE} research plan with FinanceMCP and report-ready output"
fi

if [[ -z "$DELIVERABLE" ]]; then
  DELIVERABLE="candidate shortlist, thesis, risks, and delivery-ready report"
fi

if [[ "$ENGINE" == "auto" ]]; then
  DERIVATIVES_SENSITIVE="false"
  if [[ "$INSTRUMENT" == "derivative" || "$DEPTH" == "derivatives" || "$MARKET" == "options" ]]; then
    DERIVATIVES_SENSITIVE="true"
  fi
  HUNT_SPECIALIZATION="false"
  if [[ ( "$ALPHA_MODE" == "hunt" || "$ALPHA_MODE" == "lead-follow" ) && ( "$STYLE" == "short" || "$DERIVATIVES_SENSITIVE" == "true" ) ]]; then
    HUNT_SPECIALIZATION="true"
  fi

  if [[ "$STYLE" == "short" || "$HUNT_SPECIALIZATION" == "true" ]]; then
    ENGINE="deep-research"
  else
    ENGINE="hybrid"
  fi
fi

BOOTSTRAP_PRESET="$PRESET"
POST_SHORT_BATCH="false"
POST_SHORT_ALPHA_MODE=""
REQUIRE_NATIVE_BRIEFS="false"
DERIVATIVES_SENSITIVE="false"
HUNT_SPECIALIZATION="false"
SHORT_ALPHA_GENERAL_ENABLED="false"

if [[ "$INSTRUMENT" == "derivative" || "$DEPTH" == "derivatives" || "$MARKET" == "options" ]]; then
  DERIVATIVES_SENSITIVE="true"
fi

if [[ ( "$ALPHA_MODE" == "hunt" || "$ALPHA_MODE" == "lead-follow" ) && ( "$STYLE" == "short" || "$DERIVATIVES_SENSITIVE" == "true" ) ]]; then
  HUNT_SPECIALIZATION="true"
fi

case "$HORIZON" in
  h24-48|d3-7|w1-2|w2-4|m1-3)
    SHORT_ALPHA_GENERAL_ENABLED="true"
    ;;
esac

if [[ "$HORIZON" == "auto" ]]; then
  if [[ "$STYLE" == "short" ]]; then
    case "$MARKET" in
      us|futures|options|crypto|fx)
        HORIZON="h24-48"
        ;;
      *)
        HORIZON="d3-7"
        ;;
    esac
  else
    case "$INSTRUMENT" in
      commodity|index)
        HORIZON="m3-6"
        ;;
      *)
        HORIZON="m1-3"
        ;;
    esac
  fi
fi

if [[ -z "$SCOPE" ]]; then
  SCOPE="market=${MARKET}; style=${STYLE}; alpha_mode=${ALPHA_MODE}; horizon=${HORIZON}; depth=${DEPTH}; instrument=${INSTRUMENT}; use FinanceMCP first, then web verification"
fi

if [[ "$ENGINE" == "deep-research" && "$PRESET" == "auto" ]]; then
  if [[ "$HUNT_SPECIALIZATION" == "true" ]]; then
    BOOTSTRAP_PRESET="none"
    POST_SHORT_BATCH="true"
    POST_SHORT_ALPHA_MODE="$ALPHA_MODE"
  elif [[ "$STYLE" == "short" ]]; then
    BOOTSTRAP_PRESET="high-throughput"
  else
    BOOTSTRAP_PRESET="default"
  fi
elif [[ "$ENGINE" == "superpowers" && "$PRESET" == "auto" ]]; then
  BOOTSTRAP_PRESET="default"
fi

if [[ "$ENGINE" == "deep-research" ]]; then
  REQUIRE_NATIVE_BRIEFS="true"
fi

case "$ENGINE" in
  hybrid)
    CMD=(
      bash "$TASK_BOOTSTRAP"
      "$TASK_SLUG"
      "market-alpha-orchestrator"
      "$REASON"
    )
    ;;
  superpowers)
    CMD=(
      bash "$SUPERPOWERS_BOOTSTRAP"
      "$TASK_SLUG"
      "$REASON"
      --objective "$OBJECTIVE"
      --deliverable "$DELIVERABLE"
      --scope "$SCOPE"
      --preset "$BOOTSTRAP_PRESET"
    )
    ;;
  deep-research)
    CMD=(
      bash "$DEEP_RESEARCH_BOOTSTRAP"
      "$TASK_SLUG"
      "$REASON"
      --objective "$OBJECTIVE"
      --deliverable "$DELIVERABLE"
      --scope "$SCOPE"
      --preset "$BOOTSTRAP_PRESET"
    )
    ;;
  *)
    echo "Error: unsupported engine '$ENGINE'" >&2
    exit 1
    ;;
esac

if [[ -n "$NOTE" && "$ENGINE" != "hybrid" ]]; then
  CMD+=(--note "$NOTE")
fi

echo "MARKET_ALPHA_BOOTSTRAP"
echo "TASK_SLUG=$TASK_SLUG"
echo "ENGINE=$ENGINE"
echo "MARKET=$MARKET"
echo "STYLE=$STYLE"
echo "ALPHA_MODE=$ALPHA_MODE"
echo "HORIZON=$HORIZON"
echo "DEPTH=$DEPTH"
echo "INSTRUMENT=$INSTRUMENT"
echo "PRESET=$BOOTSTRAP_PRESET"
printf 'COMMAND='
printf '%q ' "${CMD[@]}"
printf '\n'
printf 'QUANT_SETUP='
printf '%q ' python3 "$QUANT_SETUP" --task-slug "$TASK_SLUG" --style "$STYLE" --horizon "$HORIZON" --objective "$OBJECTIVE"
printf '\n'
printf 'DATA_LAYER_SETUP='
printf '%q ' python3 "$DATA_LAYER_SETUP" bootstrap-task --task-slug "$TASK_SLUG" --market "$MARKET" --style "$STYLE" --instrument "$INSTRUMENT" --horizon "$HORIZON" --alpha-mode "$ALPHA_MODE" --objective "$OBJECTIVE"
printf '\n'
if [[ "$POST_SHORT_BATCH" == "true" ]]; then
  printf 'POST_HOOK='
  printf '%q ' bash "$SCRIPT_DIR/market-alpha-short-batch.sh" --task-slug "$TASK_SLUG" --market "$MARKET" --alpha-mode "$POST_SHORT_ALPHA_MODE" --horizon "$HORIZON" --objective "$OBJECTIVE"
  printf '\n'
fi
if [[ "$SHORT_ALPHA_GENERAL_ENABLED" == "true" ]]; then
  printf 'SHORT_ALPHA_GENERAL_HOOK='
  printf '%q ' bash "$SHORT_ALPHA_GENERAL_BOOTSTRAP" --task-slug "$TASK_SLUG" --market "$MARKET" --horizon "$HORIZON" --style "$STYLE" --objective "$OBJECTIVE"
  printf '\n'
fi
printf 'NATIVE_SUBAGENTS_PREP='
if [[ "$REQUIRE_NATIVE_BRIEFS" == "true" ]]; then
  printf '%q ' python3 "$NATIVE_SUBAGENTS_PREP" --task-slug "$TASK_SLUG" --require-briefs
else
  printf '%q ' python3 "$NATIVE_SUBAGENTS_PREP" --task-slug "$TASK_SLUG"
fi
printf '\n'
printf 'NATIVE_COORDINATOR_VALIDATE='
printf '%q ' python3 "$NATIVE_COORDINATOR" validate --task-slug "$TASK_SLUG"
printf '\n'
printf 'NATIVE_COORDINATOR_STATUS='
printf '%q ' python3 "$NATIVE_COORDINATOR" status --task-slug "$TASK_SLUG"
printf '\n'

if [[ "$DRY_RUN" == "true" ]]; then
  exit 0
fi

"${CMD[@]}"

ACTIVE_SKILL="$ENGINE"
case "$ACTIVE_SKILL" in
  hybrid)
    ACTIVE_SKILL="market-alpha-orchestrator"
    ;;
  superpowers)
    ACTIVE_SKILL="superpowers"
    ;;
  deep-research)
    ACTIVE_SKILL="deep-research"
    ;;
esac

if [[ "$ACTIVE_SKILL" == "deep-research" || "$ACTIVE_SKILL" == "superpowers" ]]; then
  TASK_ORCH_CMD=(
    python3 "$TASK_ORCHESTRATION" bootstrap
    --task-slug "$TASK_SLUG"
    --primary-skill "market-alpha-orchestrator"
    --active-skill "$ACTIVE_SKILL"
    --delegated-skill "$ACTIVE_SKILL"
    --reason "$REASON"
    --mode "$ENGINE"
    --phase "research"
  )
  if [[ "$SHORT_ALPHA_GENERAL_ENABLED" == "true" ]]; then
    TASK_ORCH_CMD+=(--delegated-skill "short-alpha-general")
  fi
  "${TASK_ORCH_CMD[@]}"
else
  TASK_ORCH_CMD=(
    python3 "$TASK_ORCHESTRATION" bootstrap
    --task-slug "$TASK_SLUG"
    --primary-skill "market-alpha-orchestrator"
    --active-skill "market-alpha-orchestrator"
    --reason "$REASON"
    --mode "$ENGINE"
    --phase "research"
  )
  if [[ "$SHORT_ALPHA_GENERAL_ENABLED" == "true" ]]; then
    TASK_ORCH_CMD+=(--delegated-skill "short-alpha-general")
  fi
  "${TASK_ORCH_CMD[@]}"
fi

python3 "$QUANT_SETUP" \
  --task-slug "$TASK_SLUG" \
  --style "$STYLE" \
  --horizon "$HORIZON" \
  --objective "$OBJECTIVE"

python3 "$DATA_LAYER_SETUP" \
  bootstrap-task \
  --task-slug "$TASK_SLUG" \
  --market "$MARKET" \
  --style "$STYLE" \
  --instrument "$INSTRUMENT" \
  --horizon "$HORIZON" \
  --alpha-mode "$ALPHA_MODE" \
  --objective "$OBJECTIVE"

if [[ "$POST_SHORT_BATCH" == "true" ]]; then
  bash "$SCRIPT_DIR/market-alpha-short-batch.sh" \
    --task-slug "$TASK_SLUG" \
    --market "$MARKET" \
    --alpha-mode "$POST_SHORT_ALPHA_MODE" \
    --horizon "$HORIZON" \
    --objective "$OBJECTIVE"
fi

if [[ "$SHORT_ALPHA_GENERAL_ENABLED" == "true" ]]; then
  bash "$SHORT_ALPHA_GENERAL_BOOTSTRAP" \
    --task-slug "$TASK_SLUG" \
    --market "$MARKET" \
    --horizon "$HORIZON" \
    --style "$STYLE" \
    --objective "$OBJECTIVE"
fi

NATIVE_SUBAGENTS_ARGS=(
  "$NATIVE_SUBAGENTS_PREP"
  --task-slug "$TASK_SLUG"
)

if [[ "$REQUIRE_NATIVE_BRIEFS" == "true" ]]; then
  NATIVE_SUBAGENTS_ARGS+=(--require-briefs)
fi

python3 "${NATIVE_SUBAGENTS_ARGS[@]}"

if [[ "$REQUIRE_NATIVE_BRIEFS" == "true" ]]; then
  python3 "$TASK_ORCHESTRATION" status --task-slug "$TASK_SLUG" >/dev/null
fi

if [[ "$REQUIRE_NATIVE_BRIEFS" == "true" ]]; then
  python3 "$NATIVE_COORDINATOR" validate --task-slug "$TASK_SLUG"
fi
