#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = SCRIPT_DIR.parent.parent.parent
TASK_SCRIPT_DIR = WORKSPACE_DIR / "scripts"
sys.path.insert(0, str(TASK_SCRIPT_DIR))

import task_session  # noqa: E402
from search_backend_cooldown import maybe_record_search_backend_cooldown  # noqa: E402

DEFAULT_MODEL_CHAIN = [
    "zai/glm-4.7-flash",
    "zai/glm-4.7-flashx",
    "zai/glm-4.7",
]


def slugify(value: str) -> str:
    cleaned = []
    last_dash = False
    for ch in value.lower():
        if ch.isalnum():
            cleaned.append(ch)
            last_dash = False
        else:
            if not last_dash:
                cleaned.append("-")
                last_dash = True
    return "".join(cleaned).strip("-") or "agent"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def append_agent_status(task_dir: Path, agent_name: str, role: str, status: str, output_path: str, note: str) -> None:
    payload = {
        "timestamp_utc": task_session.iso_now(),
        "agent_name": agent_name,
        "role": role,
        "status": status,
        "output_paths": [output_path] if output_path else [],
        "note": note,
    }
    task_session.append_jsonl(task_dir / "agents.jsonl", payload)
    maybe_record_search_backend_cooldown(task_dir=task_dir, status=status, text=note)


def resolve_source_config_path(explicit: str | None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    env_path = os.environ.get("OPENCLAW_CONFIG_PATH")
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend(
        [
            WORKSPACE_DIR.parent / "config" / "openclaw.json",
            Path("/home/node/.openclaw/openclaw.json"),
            Path("/mnt/500G-1/clawdata/config/openclaw.json"),
        ]
    )
    seen: set[str] = set()
    for path in candidates:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        if path.exists():
            return path
    raise SystemExit(
        "Could not resolve OpenClaw config path. Checked: "
        + ", ".join(str(path) for path in candidates)
    )


def resolve_auth_source(config_path: Path) -> Path:
    state_dir_env = os.environ.get("OPENCLAW_STATE_DIR")
    candidates = []
    if state_dir_env:
        candidates.append(Path(state_dir_env) / "agents" / "main" / "agent" / "auth-profiles.json")
    candidates.extend(
        [
            config_path.parent / "agents" / "main" / "agent" / "auth-profiles.json",
            WORKSPACE_DIR.parent / "config" / "agents" / "main" / "agent" / "auth-profiles.json",
            Path("/home/node/.openclaw/agents/main/agent/auth-profiles.json"),
            Path("/mnt/500G-1/clawdata/config/agents/main/agent/auth-profiles.json"),
        ]
    )
    seen: set[str] = set()
    for path in candidates:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        if path.exists():
            return path
    raise SystemExit(
        "Could not resolve auth-profiles.json. Checked: "
        + ", ".join(str(path) for path in candidates)
    )


def build_minimal_config(source_config_path: Path, workspace: Path, timeout_seconds: int, model_ref: str) -> dict[str, Any]:
    source = read_json(source_config_path)
    providers = source.get("models", {}).get("providers", {})
    tools = source.get("tools", {"profile": "coding", "alsoAllow": ["group:web"]})
    return {
        "models": {
            "mode": source.get("models", {}).get("mode", "merge"),
            "providers": providers,
        },
        "agents": {
            "defaults": {
                "model": {"primary": model_ref},
                "workspace": str(workspace),
                "timeoutSeconds": timeout_seconds,
                "compaction": {"mode": "safeguard"},
                "maxConcurrent": 1,
                "subagents": {"maxConcurrent": 1},
            }
        },
        "tools": tools,
    }


def build_prompt(
    task_capsule: str,
    skill_brief: str,
    agent_brief: str,
    summary_relpath: str,
    worklog_relpath: str,
    raw_relpath: str,
) -> str:
    return (
        "You are a single worker executing one market-alpha agent brief.\n"
        "Your primary context is embedded below. Do not restate it.\n"
        "If needed, you may still use linked local directories ./scratch ./reports ./research ./sources ./scripts and ./market-alpha-skill/references/*.\n"
        f"Persist useful findings during research to `{worklog_relpath}` as you confirm them.\n"
        f"Write the final cleaned synthesis to `{summary_relpath}`.\n"
        f"If you produce structured machine-readable evidence, store it under `{raw_relpath}` or a nearby task-local file.\n"
        "Do not keep important findings only in the final reply; land them in task-local files while you work.\n"
        "Do not narrate fake progress.\n"
        "Return the substantive result directly as markdown in your final answer.\n"
        "If blocked, start the final answer with BLOCKED: and explain the blocker briefly.\n"
        "If quant work is required, use local scripts and reports/quant outputs, then summarize the evidence in markdown.\n"
        "\n"
        "## Task Capsule\n"
        f"{task_capsule}\n\n"
        "## Skill Brief\n"
        f"{skill_brief}\n\n"
        "## Agent Brief\n"
        f"{agent_brief}\n"
    )


def compact_text(text: str, max_chars: int) -> str:
    trimmed = text.strip()
    if len(trimmed) <= max_chars:
        return trimmed
    return trimmed[:max_chars].rstrip() + "\n...[truncated]"


def compact_capsule(text: str) -> str:
    keep_lines = []
    blocked_headers = {
        "## Working notes",
        "## 已完成的调研工作",
        "**已完成的调研工作**：",
    }
    for line in text.splitlines():
        if line.strip() in blocked_headers:
            break
        keep_lines.append(line)
    return compact_text("\n".join(keep_lines), 3000)


def compact_skill_brief(text: str) -> str:
    return compact_text(text, 1800)


def compact_agent_brief(text: str) -> str:
    return compact_text(text, 2400)


def unique_session_id(agent_name: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"market-alpha-{slugify(agent_name)}-{stamp}"


def unique_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def build_output_bundle(task_dir: Path, agent_brief: Path) -> dict[str, Path]:
    agent_slug = slugify(agent_brief.stem)
    research_dir = task_dir / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    return {
        "summary": research_dir / f"{agent_slug}.md",
        "worklog": research_dir / f"{agent_slug}.worklog.md",
        "raw": research_dir / f"{agent_slug}.raw.json",
        "runner_raw": task_dir / ".runner" / agent_slug / "last-run.json",
    }


def prepare_runner(task_dir: Path, agent_brief: Path, config_path: Path, timeout_seconds: int, model_ref: str) -> tuple[Path, Path, Path]:
    agent_slug = slugify(agent_brief.stem)
    runner_root = task_dir / ".runner" / agent_slug / unique_run_id()
    runner_workspace = runner_root / "workspace"
    runner_state = runner_root / "state"
    runner_workspace.mkdir(parents=True, exist_ok=True)
    runner_state.mkdir(parents=True, exist_ok=True)

    auth_source = resolve_auth_source(config_path)
    auth_target = runner_state / "agents" / "main" / "agent" / "auth-profiles.json"
    auth_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(auth_source, auth_target)

    runner_config = runner_state / "openclaw.json"
    runner_config.write_text(
        json.dumps(build_minimal_config(config_path, runner_workspace, timeout_seconds, model_ref), ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    write_text(runner_workspace / "AGENTS.md", "Operate as a terse market-alpha worker. Follow the local brief and write real output.")
    write_text(runner_workspace / "SOUL.md", "Direct, terse, execution-focused.")
    write_text(runner_workspace / "USER.md", "# USER\n- Name: market-alpha-runner")
    write_text(runner_workspace / "IDENTITY.md", "# IDENTITY\n- Name: market-alpha-runner")
    write_text(runner_workspace / "TOOLS.md", "")
    write_text(runner_workspace / "HEARTBEAT.md", "")
    write_text(runner_workspace / "MEMORY.md", "")

    shutil.copy2(task_dir / "capsules" / "task-capsule.md", runner_workspace / "task-capsule.md")
    shutil.copy2(task_dir / "capsules" / "skill-brief.md", runner_workspace / "skill-brief.md")
    shutil.copy2(agent_brief, runner_workspace / "agent-brief.md")

    for name in ["scratch", "reports", "research", "sources", "scripts"]:
        src = task_dir / name
        dst = runner_workspace / name
        if dst.exists() or dst.is_symlink():
            if dst.is_dir() and not dst.is_symlink():
                shutil.rmtree(dst)
            else:
                dst.unlink()
        if src.exists():
            dst.symlink_to(src, target_is_directory=True)

    skill_link = runner_workspace / "market-alpha-skill"
    if skill_link.exists() or skill_link.is_symlink():
        skill_link.unlink()
    skill_link.symlink_to(SCRIPT_DIR.parent, target_is_directory=True)

    return runner_state, runner_workspace, runner_config


def is_retryable(text: str) -> bool:
    lowered = text.lower()
    return "rate limit" in lowered or "timed out" in lowered or "timeout" in lowered


def run_openclaw_once(
    runner_workspace: Path,
    runner_state: Path,
    runner_config: Path,
    timeout_seconds: int,
    prompt: str,
    agent_name: str,
) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "OPENCLAW_STATE_DIR": str(runner_state),
        "OPENCLAW_CONFIG_PATH": str(runner_config),
        "OPENCLAW_HOME": str(runner_state.parent / "home"),
    }
    command = [
        "openclaw",
        "agent",
        "--local",
        "--agent",
        "main",
        "--session-id",
        unique_session_id(agent_name),
        "--message",
        prompt,
        "--json",
        "--thinking",
        "off",
        "--timeout",
        str(timeout_seconds),
    ]
    return subprocess.run(
        command,
        cwd=runner_workspace,
        env=env,
        capture_output=True,
        text=True,
        timeout=max(60, timeout_seconds + 60),
        check=False,
    )


def parse_model_chain(raw: str) -> list[str]:
    items = [item.strip() for item in raw.split(",") if item.strip()]
    return items or DEFAULT_MODEL_CHAIN


def run_agent_once(
    task_dir: Path,
    agent_brief: Path,
    config_path: Path,
    timeout_seconds: int,
    model_chain: list[str],
) -> dict[str, Any]:
    output_bundle = build_output_bundle(task_dir, agent_brief)
    summary_relpath = f"./{output_bundle['summary'].relative_to(task_dir)}"
    worklog_relpath = f"./{output_bundle['worklog'].relative_to(task_dir)}"
    raw_relpath = f"./{output_bundle['raw'].relative_to(task_dir)}"
    if not output_bundle["worklog"].exists():
        write_text(
            output_bundle["worklog"],
            "\n".join(
                [
                    f"# {agent_brief.stem} Worklog",
                    "",
                    f"- Agent: `{agent_brief.stem}`",
                    f"- Started at UTC: `{task_session.iso_now()}`",
                    "",
                    "## Live Findings",
                    "",
                    "- Initialized.",
                ]
            ),
        )
    result: subprocess.CompletedProcess[str] | None = None
    last_runner_workspace = ""
    last_runner_state = ""
    last_model = ""

    for model_ref in model_chain:
        runner_state, runner_workspace, runner_config = prepare_runner(
            task_dir=task_dir,
            agent_brief=agent_brief,
            config_path=config_path,
            timeout_seconds=timeout_seconds,
            model_ref=model_ref,
        )
        last_runner_workspace = str(runner_workspace)
        last_runner_state = str(runner_state)
        last_model = model_ref
        task_capsule_text = compact_capsule((runner_workspace / "task-capsule.md").read_text(encoding="utf-8"))
        skill_brief_text = compact_skill_brief((runner_workspace / "skill-brief.md").read_text(encoding="utf-8"))
        agent_brief_text = compact_agent_brief((runner_workspace / "agent-brief.md").read_text(encoding="utf-8"))
        prompt = build_prompt(
            task_capsule_text,
            skill_brief_text,
            agent_brief_text,
            summary_relpath=summary_relpath,
            worklog_relpath=worklog_relpath,
            raw_relpath=raw_relpath,
        )
        attempts = 2
        for attempt in range(1, attempts + 1):
            result = run_openclaw_once(
                runner_workspace=runner_workspace,
                runner_state=runner_state,
                runner_config=runner_config,
                timeout_seconds=timeout_seconds,
                prompt=prompt,
                agent_name=agent_brief.stem,
            )
            retry_blob = f"{result.stdout}\n{result.stderr}"
            if result.returncode == 0 and not is_retryable(retry_blob):
                break
            if attempt < attempts and is_retryable(retry_blob):
                time.sleep(5 * attempt)
        if result is not None:
            retry_blob = f"{result.stdout}\n{result.stderr}"
            if result.returncode == 0 and not is_retryable(retry_blob):
                break

    assert result is not None

    if result.returncode != 0:
        return {
            "ok": False,
            "stderr": result.stderr,
            "stdout": result.stdout,
            "runner_workspace": last_runner_workspace,
            "runner_state": last_runner_state,
            "model": last_model,
        }

    payload = json.loads(result.stdout)
    text_payloads = payload.get("payloads", [])
    final_text = "\n".join(item.get("text", "") for item in text_payloads if item.get("text"))
    stop_reason = payload.get("meta", {}).get("stopReason", "")
    if stop_reason == "error" or final_text.strip().startswith("⚠️") or final_text.strip().startswith("BLOCKED:"):
        return {
            "ok": False,
            "stderr": final_text or result.stderr or "worker returned error payload",
            "stdout": result.stdout,
            "runner_workspace": last_runner_workspace,
            "runner_state": last_runner_state,
            "model": last_model,
        }
    output_path = output_bundle["summary"]
    write_text(
        output_path,
        "\n".join(
            [
                final_text or "BLOCKED: empty worker output",
                "",
                "---",
                "",
                f"- Worklog path: `{worklog_relpath}`",
                f"- Structured payload path: `{raw_relpath}`",
            ]
        ),
    )
    raw_path = output_bundle["runner_raw"]
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    write_text(raw_path, json.dumps(payload, ensure_ascii=False, indent=2))
    write_text(output_bundle["raw"], json.dumps(payload, ensure_ascii=False, indent=2))
    return {
        "ok": True,
        "output_path": str(output_path),
        "worklog_path": str(output_bundle["worklog"]),
        "structured_path": str(output_bundle["raw"]),
        "runner_workspace": last_runner_workspace,
        "runner_state": last_runner_state,
        "model": last_model,
        "final_text": final_text,
    }


def cmd_run_agent(args: argparse.Namespace) -> int:
    task_dir = task_session.resolve_task_dir(task_slug=args.task_slug, prefer_active=True)
    agent_slug = slugify(args.agent_name)
    agent_brief = task_dir / "agents" / f"{agent_slug}.md"
    if not agent_brief.exists():
        raise SystemExit(f"agent brief not found: {agent_brief}")
    result = run_agent_once(
        task_dir=task_dir,
        agent_brief=agent_brief,
        config_path=Path(args.config_path),
        timeout_seconds=args.timeout,
        model_chain=parse_model_chain(args.model),
    )
    if not result["ok"]:
        append_agent_status(task_dir, args.agent_name, args.role or "", "error", "", result["stderr"])
        print("MARKET_ALPHA_AGENT_RUN_FAIL")
        print(f"AGENT={args.agent_name}")
        print(result["stderr"])
        return 1
    append_agent_status(
        task_dir,
        args.agent_name,
        args.role or "",
        "completed",
        result["output_path"],
        f"runner_workspace={result['runner_workspace']} model={result.get('model','')}",
    )
    print("MARKET_ALPHA_AGENT_RUN_OK")
    print(f"AGENT={args.agent_name}")
    print(f"OUTPUT={result['output_path']}")
    return 0


def cmd_run_batch(args: argparse.Namespace) -> int:
    task_dir = task_session.resolve_task_dir(task_slug=args.task_slug, prefer_active=True)
    briefs = sorted((task_dir / "agents").glob("*.md"))
    if args.agents:
        wanted = {slugify(item) for item in args.agents}
        briefs = [brief for brief in briefs if slugify(brief.stem) in wanted]
    if not briefs:
        raise SystemExit("no agent briefs selected")

    results = []
    with ThreadPoolExecutor(max_workers=max(1, args.parallel)) as pool:
        future_map = {
            pool.submit(
                run_agent_once,
                task_dir,
                brief,
                Path(args.config_path),
                args.timeout,
                parse_model_chain(args.model),
            ): brief
            for brief in briefs
        }
        for future in as_completed(future_map):
            brief = future_map[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {"ok": False, "stderr": str(exc), "stdout": "", "runner_workspace": ""}
            agent_name = brief.stem
            role = ""
            if result["ok"]:
                append_agent_status(task_dir, agent_name, role, "completed", result["output_path"], f"runner_workspace={result['runner_workspace']} model={result.get('model','')}")
            else:
                append_agent_status(task_dir, agent_name, role, "error", "", result["stderr"])
            results.append({"agent": agent_name, **result})

    ok = [item for item in results if item["ok"]]
    failed = [item for item in results if not item["ok"]]
    print("MARKET_ALPHA_BATCH_RUN")
    print(f"TASK_DIR={task_dir}")
    print(f"COMPLETED={len(ok)}")
    print(f"FAILED={len(failed)}")
    for item in ok:
        print(f"OK_AGENT={item['agent']} OUTPUT={item['output_path']}")
    for item in failed:
        print(f"FAILED_AGENT={item['agent']} STDERR={item['stderr'][:300]}")
    return 0 if not failed else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run market-alpha agent briefs through isolated OpenClaw local workers")
    parser.add_argument("--config-path")
    parser.add_argument("--model", default="zai/glm-4.7-flash,zai/glm-4.7-flashx,zai/glm-4.7")
    parser.add_argument("--timeout", type=int, default=120)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_agent = subparsers.add_parser("run-agent")
    run_agent.add_argument("--task-slug")
    run_agent.add_argument("--agent-name", required=True)
    run_agent.add_argument("--role")
    run_agent.set_defaults(func=cmd_run_agent)

    run_batch = subparsers.add_parser("run-batch")
    run_batch.add_argument("--task-slug")
    run_batch.add_argument("--agents", nargs="*")
    run_batch.add_argument("--parallel", type=int, default=1)
    run_batch.set_defaults(func=cmd_run_batch)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.config_path = str(resolve_source_config_path(args.config_path))
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
