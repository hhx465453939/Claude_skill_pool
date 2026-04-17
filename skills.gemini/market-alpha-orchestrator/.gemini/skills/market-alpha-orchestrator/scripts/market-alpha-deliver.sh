#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
DELIVER_SCRIPT="$WORKSPACE_DIR/scripts/deliver-report.sh"
REPORT_GATE="$SCRIPT_DIR/market-alpha-report-gate.py"
FINANCE_GATE="$WORKSPACE_DIR/scripts/finance-intel-report-gate.py"

usage() {
  cat <<'EOF'
Usage:
  market-alpha-deliver.sh --path <file> [options]

Options:
  --path <file>         Draft report path. Required.
  --task-slug <slug>    Optional task slug.
  --source <slug>       Source tag. Default: market-alpha
  --dry-run             Print resolved delivery plan without executing.
  --help                Show this message.
EOF
}

PATH_ARG=""
TASK_SLUG=""
SOURCE_ARG="market-alpha"
DRY_RUN="false"

resolve_task_dir() {
  local source_path="${1:-}"
  local probe=""
  local match=""

  if [[ -n "$source_path" ]]; then
    probe="$(dirname "$source_path")"
    while [[ "$probe" != "/" ]]; do
      if [[ "$(basename "$(dirname "$probe")")" == "tasks" ]]; then
        printf '%s\n' "$probe"
        return 0
      fi
      probe="$(dirname "$probe")"
    done
  fi

  if [[ -n "$TASK_SLUG" && -d "$WORKSPACE_DIR/tasks" ]]; then
    match="$(find "$WORKSPACE_DIR/tasks" -maxdepth 1 -mindepth 1 -type d -name "*-$TASK_SLUG" | sort | tail -n 1)"
    if [[ -n "$match" ]]; then
      printf '%s\n' "$match"
      return 0
    fi
  fi

  return 1
}

to_workspace_relative() {
  local abs_path="${1:-}"
  if [[ -z "$abs_path" ]]; then
    return 1
  fi
  if [[ "$abs_path" == "$WORKSPACE_DIR"/* ]]; then
    printf '.%s\n' "${abs_path#$WORKSPACE_DIR}"
    return 0
  fi
  printf '%s\n' "$abs_path"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --path)
      PATH_ARG="${2:-}"
      shift 2
      ;;
    --task-slug)
      TASK_SLUG="${2:-}"
      shift 2
      ;;
    --source)
      SOURCE_ARG="${2:-}"
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

if [[ -z "$PATH_ARG" ]]; then
  echo "Error: --path is required" >&2
  exit 1
fi

if [[ ! -f "$PATH_ARG" ]]; then
  echo "Error: file not found: $PATH_ARG" >&2
  exit 1
fi

ABS_PATH="$(realpath "$PATH_ARG")"
REPORT_ROOT="$(realpath "$WORKSPACE_DIR/report")"
INPUT_FOR_DELIVERY="$ABS_PATH"
TEMP_COPY=""
TASK_DIR_RESOLVED="$(resolve_task_dir "$ABS_PATH" || true)"
TASK_PATH_REL=""

if [[ -n "$TASK_DIR_RESOLVED" ]]; then
  TASK_PATH_REL="$(to_workspace_relative "$TASK_DIR_RESOLVED")"
fi

if [[ "$ABS_PATH" == "$REPORT_ROOT"/* ]]; then
  BASENAME="$(basename "$ABS_PATH")"
  if [[ "$BASENAME" != *"-generated-report-market-alpha."* ]]; then
    TEMP_COPY="$(mktemp "/tmp/market-alpha-deliver-XXXXXX.md")"
    cp "$ABS_PATH" "$TEMP_COPY"
    INPUT_FOR_DELIVERY="$TEMP_COPY"
  fi
fi

CMD=(bash "$DELIVER_SCRIPT" --path "$INPUT_FOR_DELIVERY" --source "$SOURCE_ARG")
if [[ -n "$TASK_SLUG" ]]; then
  CMD+=(--task-slug "$TASK_SLUG")
fi

echo "MARKET_ALPHA_DELIVER"
echo "INPUT=$ABS_PATH"
echo "DELIVERY_INPUT=$INPUT_FOR_DELIVERY"
if [[ -n "$TASK_DIR_RESOLVED" ]]; then
  echo "TASK_DIR=$TASK_DIR_RESOLVED"
  echo "TASK_PATH=$TASK_PATH_REL"
fi
printf 'COMMAND='
printf '%q ' "${CMD[@]}"
printf '\n'
printf 'FINANCE_GATE='
printf '%q ' python3 "$FINANCE_GATE" --report "$ABS_PATH"
if [[ -n "$TASK_SLUG" ]]; then
  printf '%q ' --task-slug "$TASK_SLUG"
fi
printf '\n'

if [[ "$DRY_RUN" == "true" ]]; then
  if [[ -n "$TEMP_COPY" && -f "$TEMP_COPY" ]]; then
    rm -f "$TEMP_COPY"
  fi
  exit 0
fi

FINANCE_GATE_CMD=(python3 "$FINANCE_GATE" --report "$ABS_PATH")
if [[ -n "$TASK_SLUG" ]]; then
  FINANCE_GATE_CMD+=(--task-slug "$TASK_SLUG")
fi
"${FINANCE_GATE_CMD[@]}"

GATE_CMD=(python3 "$REPORT_GATE" --report "$ABS_PATH")
if [[ -n "$TASK_SLUG" ]]; then
  GATE_CMD+=(--task-slug "$TASK_SLUG")
fi
"${GATE_CMD[@]}"

OUTPUT="$("${CMD[@]}")"
printf '%s\n' "$OUTPUT"

FILEPATH_LINE="$(printf '%s\n' "$OUTPUT" | rg '^FILEPATH:' -N -m 1 || true)"
if [[ -n "$FILEPATH_LINE" ]]; then
  REL_PATH="${FILEPATH_LINE#FILEPATH:}"
  REL_PATH="${REL_PATH#./}"
  echo "FEISHU_SEND_FILE_PAYLOAD={\"action\":\"upload_and_send\",\"file_path\":\"$REL_PATH\"}"
fi

if [[ -n "$TASK_DIR_RESOLVED" ]]; then
  echo "TASK_DIR=$TASK_DIR_RESOLVED"
  echo "TASK_PATH:$TASK_PATH_REL"
fi

if [[ -n "$TEMP_COPY" && -f "$TEMP_COPY" ]]; then
  rm -f "$TEMP_COPY"
fi
