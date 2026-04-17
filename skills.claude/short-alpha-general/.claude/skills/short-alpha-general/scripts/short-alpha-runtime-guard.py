#!/usr/bin/env python3

from __future__ import annotations

import argparse
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

from _short_alpha_common import ensure_task_dir, read_json, resolve_output, write_json


LADDER = [6, 4, 2, 1]


def default_policy(task_slug: str) -> OrderedDict:
    return OrderedDict(
        tool="short-alpha-general/runtime-guard",
        task_slug=task_slug,
        created_at_utc="",
        updated_at_utc="",
        ladder=LADDER,
        current_parallelism=6,
        mode="parallel",
        degrade_reason="",
        history=[],
    )


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def policy_path(task_dir: Path) -> Path:
    return task_dir / "results" / "runtime" / "concurrency-policy.json"


def cmd_init(args: argparse.Namespace) -> int:
    task_dir = ensure_task_dir(args.task_slug)
    payload = default_policy(args.task_slug)
    payload["created_at_utc"] = payload["updated_at_utc"] = iso_now()
    path = policy_path(task_dir)
    write_json(path, payload)
    print("SHORT_ALPHA_RUNTIME_GUARD_INIT_OK")
    print(f"OUTPUT={path}")
    return 0


def cmd_degrade(args: argparse.Namespace) -> int:
    task_dir = ensure_task_dir(args.task_slug)
    path = policy_path(task_dir)
    payload = read_json(path, default_policy(args.task_slug))
    current = int(payload.get("current_parallelism", LADDER[0]))
    next_value = 1
    for value in LADDER:
        if value < current:
            next_value = value
            break
    payload["current_parallelism"] = next_value
    payload["updated_at_utc"] = iso_now()
    payload["degrade_reason"] = str(args.reason or "").strip()
    if next_value == 1 and str(args.reason or "").strip():
        payload["mode"] = "single-thread"
    history = payload.setdefault("history", [])
    history.append(
        {
            "updated_at_utc": payload["updated_at_utc"],
            "current_parallelism": next_value,
            "reason": payload["degrade_reason"],
            "mode": payload["mode"],
        }
    )
    write_json(path, payload)
    print("SHORT_ALPHA_RUNTIME_GUARD_DEGRADE_OK")
    print(f"OUTPUT={path}")
    print(f"CURRENT_PARALLELISM={next_value}")
    return 0


def cmd_parent_only(args: argparse.Namespace) -> int:
    task_dir = ensure_task_dir(args.task_slug)
    path = policy_path(task_dir)
    payload = read_json(path, default_policy(args.task_slug))
    payload["current_parallelism"] = 1
    payload["mode"] = "parent-only"
    payload["updated_at_utc"] = iso_now()
    payload["degrade_reason"] = str(args.reason or "fallback to parent-only").strip()
    history = payload.setdefault("history", [])
    history.append(
        {
            "updated_at_utc": payload["updated_at_utc"],
            "current_parallelism": 1,
            "reason": payload["degrade_reason"],
            "mode": "parent-only",
        }
    )
    write_json(path, payload)
    print("SHORT_ALPHA_RUNTIME_GUARD_PARENT_ONLY_OK")
    print(f"OUTPUT={path}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    task_dir = ensure_task_dir(args.task_slug)
    path = policy_path(task_dir)
    payload = read_json(path, default_policy(args.task_slug))
    print("SHORT_ALPHA_RUNTIME_GUARD_STATUS")
    print(f"OUTPUT={path}")
    print(f"MODE={payload.get('mode', '')}")
    print(f"CURRENT_PARALLELISM={payload.get('current_parallelism', '')}")
    print(f"DEGRADE_REASON={payload.get('degrade_reason', '')}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage short-alpha-general adaptive concurrency policy")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("--task-slug", required=True)
    init.set_defaults(func=cmd_init)

    degrade = sub.add_parser("degrade")
    degrade.add_argument("--task-slug", required=True)
    degrade.add_argument("--reason", default="")
    degrade.set_defaults(func=cmd_degrade)

    parent_only = sub.add_parser("parent-only")
    parent_only.add_argument("--task-slug", required=True)
    parent_only.add_argument("--reason", default="")
    parent_only.set_defaults(func=cmd_parent_only)

    status = sub.add_parser("status")
    status.add_argument("--task-slug", required=True)
    status.set_defaults(func=cmd_status)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
