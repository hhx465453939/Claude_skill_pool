#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = SCRIPT_DIR.parent.parent.parent
TASK_SCRIPT_DIR = WORKSPACE_DIR / "scripts"
sys.path.insert(0, str(TASK_SCRIPT_DIR))

import task_session  # noqa: E402


REQUIRED_HEADINGS = [
    "执行摘要",
    "交易计划",
    "风险矩阵",
    "Bot Handoff",
]

REQUIRED_PLAN_MARKERS = [
    "方向",
    "入场",
    "止损",
    "止盈",
    "失效条件",
    "最大持有时长",
]

BOT_REQUIRED_KEYS = [
    "ticker",
    "direction",
    "entry_trigger",
    "entry_zone",
    "order_type",
    "stop_loss",
    "take_profit",
    "time_stop",
    "max_holding_period",
    "invalidation",
]
ETF_DEGRADATION_MARKERS = [
    "etf fallback",
    "degraded fallback",
    "etf-only degradation",
    "单名股未通过",
    "降级为 etf",
]


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def task_capsule_text(task_dir: Path) -> str:
    path = task_dir / "capsules" / "task-capsule.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def single_name_mandate_active(task_dir: Path) -> bool:
    text = task_capsule_text(task_dir).lower()
    if not text:
        return False
    return "market=us" in text and "alpha_mode=hunt" in text and ("horizon=m1-3" in text or "horizon=m3-6" in text)


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def extract_bot_handoff_payload(text: str):
    pattern = re.compile(r"##\s*Bot Handoff.*?```json\s*(.*?)\s*```", re.S)
    match = pattern.search(text)
    if not match:
        return None, "Bot Handoff json fence missing"
    raw = match.group(1).strip()
    try:
        return json.loads(raw), ""
    except json.JSONDecodeError as exc:
        return None, f"Bot Handoff json invalid: {exc}"


def normalize_bot_plans(payload):
    if isinstance(payload, list):
        return payload, ""
    if isinstance(payload, dict):
        if payload.get("status") == "NOT_EXECUTABLE":
            reason = payload.get("reason")
            missing = payload.get("missing_fields")
            if not reason or missing is None:
                return None, "NOT_EXECUTABLE handoff must include reason and missing_fields"
            return [], ""
        plans = payload.get("plans")
        if isinstance(plans, list):
            return plans, ""
    return None, "Bot Handoff must be a list of plans, a dict with plans, or NOT_EXECUTABLE payload"


def main() -> int:
    parser = argparse.ArgumentParser(description="Gate market-alpha reports before delivery")
    parser.add_argument("--report", required=True)
    parser.add_argument("--task-slug")
    parser.add_argument("--require-quant", action="store_true")
    args = parser.parse_args()

    report_path = Path(args.report).resolve()
    if not report_path.exists():
        raise SystemExit(f"report not found: {report_path}")
    text = report_path.read_text(encoding="utf-8")

    missing = [heading for heading in REQUIRED_HEADINGS if heading not in text]
    if missing:
      print("MARKET_ALPHA_REPORT_GATE_FAIL")
      print(f"REASON=missing headings: {', '.join(missing)}")
      return 2

    missing_plan_markers = [marker for marker in REQUIRED_PLAN_MARKERS if marker not in text]
    if missing_plan_markers:
        print("MARKET_ALPHA_REPORT_GATE_FAIL")
        print(f"REASON=trade plan missing markers: {', '.join(missing_plan_markers)}")
        return 3

    bot_payload, bot_error = extract_bot_handoff_payload(text)
    if bot_error:
        print("MARKET_ALPHA_REPORT_GATE_FAIL")
        print(f"REASON={bot_error}")
        return 4

    bot_plans, plans_error = normalize_bot_plans(bot_payload)
    if plans_error:
        print("MARKET_ALPHA_REPORT_GATE_FAIL")
        print(f"REASON={plans_error}")
        return 5

    if bot_plans is not None:
        for idx, plan in enumerate(bot_plans, start=1):
            if not isinstance(plan, dict):
                print("MARKET_ALPHA_REPORT_GATE_FAIL")
                print(f"REASON=Bot Handoff plan #{idx} is not an object")
                return 6
            missing_keys = [key for key in BOT_REQUIRED_KEYS if key not in plan]
            if missing_keys:
                print("MARKET_ALPHA_REPORT_GATE_FAIL")
                print(f"REASON=Bot Handoff plan #{idx} missing keys: {', '.join(missing_keys)}")
                return 7

    task_dir = None
    if args.task_slug:
        task_dir = task_session.resolve_task_dir(task_slug=args.task_slug, prefer_active=True)

    if task_dir is not None:
        agents_rows = read_jsonl(task_dir / "agents.jsonl")
        queued_only = bool(agents_rows) and all((row.get("status") or "") == "queued" for row in agents_rows)
        research_files = []
        for base in [task_dir / "research", task_dir / "reports"]:
            if base.exists():
                research_files.extend([p for p in base.rglob("*") if p.is_file()])
        if queued_only and len(research_files) <= 4:
            print("MARKET_ALPHA_REPORT_GATE_FAIL")
            print("REASON=task has only queued agent briefs and no meaningful research outputs")
            return 8

        reviewer_verdict_path = task_dir / "reports" / "review" / "reviewer-verdict.json"
        if not reviewer_verdict_path.exists():
            print("MARKET_ALPHA_REPORT_GATE_FAIL")
            print("REASON=missing reviewer verdict: reports/review/reviewer-verdict.json")
            return 12
        reviewer_verdict = read_json(reviewer_verdict_path)
        review_status = str(reviewer_verdict.get("status", "")).strip().upper()
        can_generate_report = bool(reviewer_verdict.get("can_generate_report"))
        single_name_status = str(reviewer_verdict.get("single_name_status", "")).strip().upper()
        if review_status not in {"REVIEW_PASS", "REVIEW_PASS_WITH_DEGRADATION"}:
            print("MARKET_ALPHA_REPORT_GATE_FAIL")
            print(f"REASON=reviewer verdict not passing: {review_status or '(missing)'}")
            return 13
        if not can_generate_report:
            print("MARKET_ALPHA_REPORT_GATE_FAIL")
            print("REASON=reviewer verdict blocks report generation")
            return 14
        if single_name_mandate_active(task_dir) and single_name_status not in {"HAS_SINGLE_NAME", "NO_SINGLE_NAME_PASSED", "ETF_ONLY_ALLOWED"}:
            print("MARKET_ALPHA_REPORT_GATE_FAIL")
            print(f"REASON=single-name mandate active but reviewer verdict unresolved: {single_name_status or '(missing)'}")
            return 15
        if single_name_status == "NO_SINGLE_NAME_PASSED":
            lowered_text = text.lower()
            if not any(marker in lowered_text for marker in ETF_DEGRADATION_MARKERS):
                print("MARKET_ALPHA_REPORT_GATE_FAIL")
                print("REASON=reviewer allowed ETF degradation but report does not label the degradation explicitly")
                return 16

    quant_claim = (
        "置信度" in text
        or "技术评分" in text
        or "回测" in text
        or "量化" in text
        or args.require_quant
    )

    if quant_claim:
        if "## Quant Evidence" not in text:
            print("MARKET_ALPHA_REPORT_GATE_FAIL")
            print("REASON=quant claim present but Quant Evidence section missing")
            return 9
        required_markers = [
            "Script path:",
            "Input path:",
            "Output path:",
            "Method used:",
            "Summary:",
        ]
        missing_markers = [marker for marker in required_markers if marker not in text]
        if missing_markers:
            print("MARKET_ALPHA_REPORT_GATE_FAIL")
            print(f"REASON=Quant Evidence missing fields: {', '.join(missing_markers)}")
            return 10
        path_pattern = re.compile(r"`(\./tasks/[^`]+|/mnt/500G-1/clawdata/[^`]+)`")
        paths = path_pattern.findall(text)
        missing_paths = []
        for raw in paths:
            candidate = Path(raw)
            if raw.startswith("./tasks/"):
                candidate = WORKSPACE_DIR / raw[2:]
            if not candidate.exists():
                missing_paths.append(raw)
        if missing_paths:
            print("MARKET_ALPHA_REPORT_GATE_FAIL")
            print(f"REASON=Quant Evidence references missing files: {', '.join(missing_paths)}")
            return 11

    print("MARKET_ALPHA_REPORT_GATE_OK")
    print(f"REPORT={report_path}")
    if task_dir:
        print(f"TASK_DIR={task_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
