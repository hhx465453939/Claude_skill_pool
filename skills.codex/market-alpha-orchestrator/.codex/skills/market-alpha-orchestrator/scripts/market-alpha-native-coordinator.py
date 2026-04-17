#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = SCRIPT_DIR.parent.parent.parent
TASK_SCRIPT_DIR = WORKSPACE_DIR / "scripts"
sys.path.insert(0, str(TASK_SCRIPT_DIR))

import task_session  # noqa: E402
import task_orchestration  # noqa: E402


ACTIVE_STATUSES = {"spawned", "running", "working"}
SUCCESS_STATUSES = {"completed"}
ERROR_STATUSES = {"error", "blocked", "failed", "timed-out", "timeout", "killed"}
TERMINAL_STATUSES = SUCCESS_STATUSES | ERROR_STATUSES


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        text = raw.strip()
        if not text:
            continue
        rows.append(json.loads(text))
    return rows


def rel_to_workspace(path: Path) -> str:
    return f"./{path.relative_to(WORKSPACE_DIR).as_posix()}"


def resolve_task(task_slug: str | None) -> Path:
    return task_session.resolve_task_dir(task_slug=task_slug, prefer_active=True)


def manifest_path(task_dir: Path) -> Path:
    return task_dir / "native-subagents" / "manifest.json"


def playbook_path(task_dir: Path) -> Path:
    return task_dir / "native-subagents" / "coordinator-playbook.md"


def load_manifest(task_dir: Path) -> dict[str, Any]:
    path = manifest_path(task_dir)
    if not path.exists():
        raise SystemExit(f"Missing manifest: {path}")
    return read_json(path)


def latest_rows_by_agent(task_dir: Path) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(task_dir / "agents.jsonl"):
        name = str(row.get("agent_name", "")).strip()
        if name:
            latest[name] = row
    return latest


def output_state(paths: list[str]) -> tuple[list[str], list[str]]:
    existing: list[str] = []
    missing: list[str] = []
    for raw in paths:
        candidate = raw.strip()
        if not candidate:
            continue
        path = WORKSPACE_DIR / candidate[2:] if candidate.startswith("./") else Path(candidate)
        if path.exists():
            existing.append(candidate)
        else:
            missing.append(candidate)
    return existing, missing


def build_agent_state(entry: dict[str, Any], latest_row: dict[str, Any] | None) -> dict[str, Any]:
    status = str((latest_row or {}).get("status", "queued")).strip() or "queued"
    output_paths = [path for path in entry.get("output_paths", []) if isinstance(path, str)]
    existing, missing = output_state(output_paths)
    note = str((latest_row or {}).get("note", "")).strip()
    return {
        "agent_name": str(entry.get("agent_name", "")).strip(),
        "role": str(entry.get("role", "")).strip(),
        "wave": int(entry.get("wave", 0)),
        "status": status,
        "note": note,
        "output_paths": output_paths,
        "existing_outputs": existing,
        "missing_outputs": missing,
        "spawn_payload": entry.get("spawn_payload", {}),
    }


def compute_status(task_dir: Path) -> dict[str, Any]:
    manifest = load_manifest(task_dir)
    latest_rows = latest_rows_by_agent(task_dir)
    agents = [
        build_agent_state(entry, latest_rows.get(str(entry.get("agent_name", "")).strip()))
        for entry in manifest.get("agents", [])
        if isinstance(entry, dict)
    ]

    waves: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for agent in agents:
        waves[int(agent["wave"])].append(agent)

    wave_summaries: list[dict[str, Any]] = []
    next_wave: int | None = None
    advance_ready = True
    blocked_by_errors = False
    previous_waves_completed = True

    for wave in sorted(waves):
        entries = sorted(waves[wave], key=lambda item: item["agent_name"])
        completed = sum(1 for item in entries if item["status"] in SUCCESS_STATUSES)
        active = sum(1 for item in entries if item["status"] in ACTIVE_STATUSES)
        errors = sum(1 for item in entries if item["status"] in ERROR_STATUSES)
        queued = sum(1 for item in entries if item["status"] == "queued")
        all_completed = completed == len(entries)
        any_started = any(item["status"] != "queued" for item in entries)
        wave_summary = {
            "wave": wave,
            "completed": completed,
            "active": active,
            "errors": errors,
            "queued": queued,
            "total": len(entries),
            "all_completed": all_completed,
            "any_started": any_started,
            "agents": entries,
        }
        wave_summaries.append(wave_summary)

        if errors > 0:
            blocked_by_errors = True

        if previous_waves_completed and not any_started and next_wave is None:
            next_wave = wave
            advance_ready = True
            previous_waves_completed = False
            continue

        if previous_waves_completed and not all_completed:
            next_wave = None
            advance_ready = False
            previous_waves_completed = False
            continue

        previous_waves_completed = previous_waves_completed and all_completed

    if blocked_by_errors:
        advance_ready = False
        next_wave = None

    if previous_waves_completed and wave_summaries:
        advance_ready = False
        next_wave = None

    return {
        "task_dir": str(task_dir),
        "task_path": rel_to_workspace(task_dir),
        "manifest_path": rel_to_workspace(manifest_path(task_dir)),
        "playbook_path": rel_to_workspace(playbook_path(task_dir)),
        "wave_summaries": wave_summaries,
        "next_wave": next_wave,
        "advance_ready": advance_ready,
        "blocked_by_errors": blocked_by_errors,
    }


def cmd_validate(args: argparse.Namespace) -> int:
    task_dir = resolve_task(args.task_slug)
    manifest = load_manifest(task_dir)
    errors: list[str] = []
    playbook = playbook_path(task_dir)
    if not playbook.exists():
        errors.append(f"missing playbook: {playbook}")
    agents = manifest.get("agents", [])
    if not isinstance(agents, list) or not agents:
        errors.append("manifest has no agents")
    for entry in agents if isinstance(agents, list) else []:
        if not isinstance(entry, dict):
            continue
        brief = entry.get("brief_path")
        prompt = entry.get("prompt_path")
        if isinstance(brief, str):
            brief_path = WORKSPACE_DIR / brief[2:] if brief.startswith("./") else Path(brief)
            if not brief_path.exists():
                errors.append(f"missing brief: {brief}")
        if isinstance(prompt, str):
            prompt_path = WORKSPACE_DIR / prompt[2:] if prompt.startswith("./") else Path(prompt)
            if not prompt_path.exists():
                errors.append(f"missing prompt: {prompt}")
    if errors:
        print("MARKET_ALPHA_NATIVE_COORDINATOR_INVALID")
        print(f"TASK_DIR={task_dir}")
        for error in errors:
            print(f"ERROR={error}")
        return 1

    status = compute_status(task_dir)
    print("MARKET_ALPHA_NATIVE_COORDINATOR_VALID")
    print(f"TASK_DIR={task_dir}")
    print(f"MANIFEST={status['manifest_path']}")
    print(f"PLAYBOOK={status['playbook_path']}")
    print(f"NEXT_WAVE={status['next_wave'] if status['next_wave'] is not None else 'none'}")
    return 0


def cmd_record_spawn(args: argparse.Namespace) -> int:
    task_dir = resolve_task(args.task_slug)
    manifest = load_manifest(task_dir)
    target = None
    for entry in manifest.get("agents", []):
        if isinstance(entry, dict) and str(entry.get("agent_name", "")).strip() == args.agent_name:
            target = entry
            break
    if target is None:
        raise SystemExit(f"Unknown agent in manifest: {args.agent_name}")

    note_parts = [
        "sessions_spawn accepted",
        f"runId={args.run_id}",
        f"childSessionKey={args.child_session_key}",
        f"label={target.get('spawn_label', '')}",
        f"wave={target.get('wave', '')}",
    ]
    payload = {
        "timestamp_utc": task_session.iso_now(),
        "agent_name": args.agent_name,
        "role": str(target.get("role", "")).strip(),
        "status": "spawned",
        "output_paths": [path for path in target.get("output_paths", []) if isinstance(path, str)],
        "note": "; ".join(part for part in note_parts if part),
    }
    task_session.append_jsonl(task_dir / "agents.jsonl", payload)
    task_orchestration.sync_lane(
        task_dir=task_dir,
        agent_name=args.agent_name,
        owner_skill="market-alpha-orchestrator",
        role=str(target.get("role", "")).strip(),
        status="spawned",
        output_paths=[path for path in target.get("output_paths", []) if isinstance(path, str)],
        note=payload["note"],
    )
    print("MARKET_ALPHA_NATIVE_SPAWN_RECORDED")
    print(f"TASK_DIR={task_dir}")
    print(f"AGENT={args.agent_name}")
    print(f"RUN_ID={args.run_id}")
    print(f"CHILD_SESSION_KEY={args.child_session_key}")
    return 0


def render_text_status(status: dict[str, Any]) -> str:
    lines = [
        "MARKET_ALPHA_NATIVE_STATUS",
        f"TASK_PATH={status['task_path']}",
        f"MANIFEST={status['manifest_path']}",
        f"PLAYBOOK={status['playbook_path']}",
        f"NEXT_WAVE={status['next_wave'] if status['next_wave'] is not None else 'none'}",
        f"ADVANCE_READY={'true' if status['advance_ready'] else 'false'}",
        f"BLOCKED_BY_ERRORS={'true' if status['blocked_by_errors'] else 'false'}",
    ]
    for wave_summary in status["wave_summaries"]:
        lines.append(
            "WAVE "
            + str(wave_summary["wave"])
            + " "
            + f"completed={wave_summary['completed']}/{wave_summary['total']} "
            + f"active={wave_summary['active']} "
            + f"errors={wave_summary['errors']} "
            + f"queued={wave_summary['queued']}"
        )
        for agent in wave_summary["agents"]:
            lines.append(
                "- "
                + f"{agent['agent_name']} "
                + f"status={agent['status']} "
                + f"outputs={len(agent['existing_outputs'])}/{len(agent['output_paths'])}"
            )
            if agent["note"]:
                lines.append(f"  note={agent['note']}")
    return "\n".join(lines)


def cmd_status(args: argparse.Namespace) -> int:
    task_dir = resolve_task(args.task_slug)
    status = compute_status(task_dir)
    if args.format == "json":
        print(json.dumps(status, ensure_ascii=False, indent=2))
    else:
        print(render_text_status(status))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect and persist market-alpha native subagent orchestration state")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--task-slug")
    validate.set_defaults(func=cmd_validate)

    record_spawn = subparsers.add_parser("record-spawn")
    record_spawn.add_argument("--task-slug")
    record_spawn.add_argument("--agent-name", required=True)
    record_spawn.add_argument("--run-id", required=True)
    record_spawn.add_argument("--child-session-key", required=True)
    record_spawn.set_defaults(func=cmd_record_spawn)

    status = subparsers.add_parser("status")
    status.add_argument("--task-slug")
    status.add_argument("--format", choices=["text", "json"], default="text")
    status.set_defaults(func=cmd_status)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
