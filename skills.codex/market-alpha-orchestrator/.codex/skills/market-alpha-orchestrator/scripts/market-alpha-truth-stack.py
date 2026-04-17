#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from collections import OrderedDict
from pathlib import Path
import sys
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = SCRIPT_DIR.parent.parent.parent
TASK_SCRIPT_DIR = WORKSPACE_DIR / "scripts"
sys.path.insert(0, str(TASK_SCRIPT_DIR))

import task_session  # noqa: E402


TRUTH_STATUSES = {"VERIFIED", "PARTIAL", "MISSING"}
REVIEW_STATUSES = {
    "REVIEW_PASS",
    "REVIEW_PASS_WITH_DEGRADATION",
    "REVIEW_FAIL",
    "REVIEW_BLOCKED",
}
SINGLE_NAME_STATUSES = {
    "REQUIRED",
    "HAS_SINGLE_NAME",
    "NO_SINGLE_NAME_PASSED",
    "ETF_ONLY_ALLOWED",
    "NOT_APPLICABLE",
}


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def ensure_truth_root(task_dir: Path) -> tuple[Path, Path]:
    derivatives_dir = task_dir / "reports" / "derivatives"
    review_dir = task_dir / "reports" / "review"
    derivatives_dir.mkdir(parents=True, exist_ok=True)
    review_dir.mkdir(parents=True, exist_ok=True)
    return derivatives_dir, review_dir


def default_truth_payload(task_slug: str) -> OrderedDict[str, Any]:
    return OrderedDict(
        tool="market-alpha-truth-stack",
        task_slug=task_slug,
        created_at_utc=task_session.iso_now(),
        updated_at_utc=task_session.iso_now(),
        required_fields=[
            "symbol",
            "last_price",
            "currency",
            "as_of",
            "source_primary",
            "source_secondary",
            "cross_check_diff_pct",
            "truth_status",
            "notes",
        ],
        allowed_truth_status=sorted(TRUTH_STATUSES),
        symbols=[],
    )


def default_reviewer_payload(task_slug: str) -> OrderedDict[str, Any]:
    return OrderedDict(
        tool="market-alpha-truth-stack",
        task_slug=task_slug,
        created_at_utc=task_session.iso_now(),
        updated_at_utc=task_session.iso_now(),
        status="REVIEW_BLOCKED",
        can_generate_report=False,
        precision_summary=OrderedDict(
            underlying_truth_level="MISSING",
            structure_precision_level="THEME_ONLY",
            execution_status="NOT_EXECUTABLE",
        ),
        single_name_status="REQUIRED",
        allowed_output="NONE",
        failures=[
            OrderedDict(
                type="uninitialized_review",
                message="Reviewer verdict has not been written yet.",
                owner="reviewer",
                required_fix="Write reviewer verdict before report delivery.",
            )
        ],
        requeue_agents=[],
        notes="Initialized by market-alpha-truth-stack.py",
    )


def load_payload(path: Path, default_payload: OrderedDict[str, Any]) -> OrderedDict[str, Any]:
    existing = task_session.read_json(path, {})
    if isinstance(existing, dict) and existing:
        return OrderedDict(existing)
    return default_payload


def cmd_init_task(args: argparse.Namespace) -> int:
    task_dir = task_session.resolve_task_dir(task_slug=args.task_slug, prefer_active=True)
    task_slug = task_dir.name.split("-", 3)[-1] if "-" in task_dir.name else task_dir.name
    derivatives_dir, review_dir = ensure_truth_root(task_dir)
    truth_path = derivatives_dir / "underlying-truth-ledger.json"
    verdict_path = review_dir / "reviewer-verdict.json"
    notes_path = review_dir / "README.md"

    truth_payload = load_payload(truth_path, default_truth_payload(task_slug))
    truth_payload["updated_at_utc"] = task_session.iso_now()
    task_session.write_json(truth_path, truth_payload)

    verdict_payload = load_payload(verdict_path, default_reviewer_payload(task_slug))
    verdict_payload["updated_at_utc"] = task_session.iso_now()
    task_session.write_json(verdict_path, verdict_payload)

    write_text(
        notes_path,
        """# Reviewer And Truth Stack

- `underlying-truth-ledger.json`
  - 记录每个标的的现货真值、时间戳、主/次来源与交叉偏差
- `reviewer-verdict.json`
  - 记录 blocking reviewer 的最终裁决

## Guardrail

- 没有 truth ledger，不要把衍生品建议包装成高精度执行单
- 没有 reviewer verdict，不要让报告进入交付
""",
    )

    print("MARKET_ALPHA_TRUTH_STACK_INIT_OK")
    print(f"TASK_DIR={task_dir}")
    print(f"TRUTH_LEDGER={truth_path}")
    print(f"REVIEWER_VERDICT={verdict_path}")
    return 0


def cmd_upsert_underlying(args: argparse.Namespace) -> int:
    task_dir = task_session.resolve_task_dir(task_slug=args.task_slug, prefer_active=True)
    task_slug = task_dir.name.split("-", 3)[-1] if "-" in task_dir.name else task_dir.name
    derivatives_dir, _review_dir = ensure_truth_root(task_dir)
    truth_path = derivatives_dir / "underlying-truth-ledger.json"
    payload = load_payload(truth_path, default_truth_payload(task_slug))
    truth_status = str(args.truth_status or "VERIFIED").strip().upper()
    if truth_status not in TRUTH_STATUSES:
        raise SystemExit(f"invalid truth status: {truth_status}")

    symbols = [item for item in payload.get("symbols", []) if isinstance(item, dict)]
    normalized_symbol = str(args.symbol).strip().upper()
    entry = OrderedDict(
        symbol=normalized_symbol,
        last_price=float(args.price),
        currency=str(args.currency or "USD").strip().upper(),
        as_of=str(args.as_of).strip(),
        source_primary=str(args.source_primary).strip(),
        source_secondary=str(args.source_secondary or "").strip(),
        cross_check_diff_pct=float(args.cross_check_diff_pct),
        truth_status=truth_status,
        notes=str(args.notes or "").strip(),
        updated_at_utc=task_session.iso_now(),
    )

    replaced = False
    for index, candidate in enumerate(symbols):
        if str(candidate.get("symbol", "")).strip().upper() == normalized_symbol:
            symbols[index] = entry
            replaced = True
            break
    if not replaced:
        symbols.append(entry)

    payload["symbols"] = symbols
    payload["updated_at_utc"] = task_session.iso_now()
    task_session.write_json(truth_path, payload)

    print("MARKET_ALPHA_TRUTH_STACK_UPSERT_OK")
    print(f"TRUTH_LEDGER={truth_path}")
    print(f"SYMBOL={normalized_symbol}")
    return 0


def cmd_write_verdict(args: argparse.Namespace) -> int:
    task_dir = task_session.resolve_task_dir(task_slug=args.task_slug, prefer_active=True)
    task_slug = task_dir.name.split("-", 3)[-1] if "-" in task_dir.name else task_dir.name
    _derivatives_dir, review_dir = ensure_truth_root(task_dir)
    verdict_path = review_dir / "reviewer-verdict.json"
    payload = load_payload(verdict_path, default_reviewer_payload(task_slug))

    if args.payload_json:
        incoming = json.loads(args.payload_json)
        if not isinstance(incoming, dict):
            raise SystemExit("payload-json must decode to an object")
        payload.update(incoming)
    else:
        status = str(args.status or payload.get("status") or "").strip().upper()
        if status and status not in REVIEW_STATUSES:
            raise SystemExit(f"invalid reviewer status: {status}")
        single_name_status = str(args.single_name_status or payload.get("single_name_status") or "").strip().upper()
        if single_name_status and single_name_status not in SINGLE_NAME_STATUSES:
            raise SystemExit(f"invalid single-name status: {single_name_status}")
        if status:
            payload["status"] = status
        if args.can_generate_report is not None:
            payload["can_generate_report"] = bool(args.can_generate_report)
        if single_name_status:
            payload["single_name_status"] = single_name_status
        if args.allowed_output:
            payload["allowed_output"] = str(args.allowed_output).strip()
        if args.note:
            payload["notes"] = str(args.note).strip()
        if args.requeue_agent:
            payload["requeue_agents"] = [str(item).strip() for item in args.requeue_agent if str(item).strip()]
        precision = payload.get("precision_summary")
        if not isinstance(precision, dict):
            precision = {}
        if args.underlying_truth_level:
            precision["underlying_truth_level"] = str(args.underlying_truth_level).strip().upper()
        if args.structure_precision_level:
            precision["structure_precision_level"] = str(args.structure_precision_level).strip().upper()
        if args.execution_status:
            precision["execution_status"] = str(args.execution_status).strip().upper()
        payload["precision_summary"] = precision
        if args.failures_json:
            failures = json.loads(args.failures_json)
            if not isinstance(failures, list):
                raise SystemExit("failures-json must decode to a list")
            payload["failures"] = failures
        elif status in {"REVIEW_PASS", "REVIEW_PASS_WITH_DEGRADATION"}:
            payload["failures"] = []

    payload["task_slug"] = task_slug
    payload["updated_at_utc"] = task_session.iso_now()
    task_session.write_json(verdict_path, payload)

    print("MARKET_ALPHA_TRUTH_STACK_VERDICT_OK")
    print(f"REVIEWER_VERDICT={verdict_path}")
    print(f"STATUS={payload.get('status', '')}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage task-local truth ledger and reviewer verdict for market-alpha tasks")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init-task")
    init.add_argument("--task-slug")
    init.set_defaults(func=cmd_init_task)

    upsert = subparsers.add_parser("upsert-underlying")
    upsert.add_argument("--task-slug")
    upsert.add_argument("--symbol", required=True)
    upsert.add_argument("--price", type=float, required=True)
    upsert.add_argument("--currency", default="USD")
    upsert.add_argument("--as-of", required=True)
    upsert.add_argument("--source-primary", required=True)
    upsert.add_argument("--source-secondary", default="")
    upsert.add_argument("--cross-check-diff-pct", type=float, default=0.0)
    upsert.add_argument("--truth-status", default="VERIFIED")
    upsert.add_argument("--notes", default="")
    upsert.set_defaults(func=cmd_upsert_underlying)

    verdict = subparsers.add_parser("write-reviewer-verdict")
    verdict.add_argument("--task-slug")
    verdict.add_argument("--payload-json")
    verdict.add_argument("--status")
    verdict.add_argument("--can-generate-report", action=argparse.BooleanOptionalAction, default=None)
    verdict.add_argument("--single-name-status")
    verdict.add_argument("--allowed-output")
    verdict.add_argument("--underlying-truth-level")
    verdict.add_argument("--structure-precision-level")
    verdict.add_argument("--execution-status")
    verdict.add_argument("--note")
    verdict.add_argument("--requeue-agent", action="append", default=[])
    verdict.add_argument("--failures-json")
    verdict.set_defaults(func=cmd_write_verdict)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
