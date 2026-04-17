#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import OrderedDict, defaultdict
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = SCRIPT_DIR.parent.parent.parent
TASK_SCRIPT_DIR = WORKSPACE_DIR / "scripts"
sys.path.insert(0, str(TASK_SCRIPT_DIR))

import task_session  # noqa: E402
from search_runtime_bridge import build_search_runtime_section  # noqa: E402


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        rows.append(json.loads(text))
    return rows


def rel_to_workspace(path: Path) -> str:
    return f"./{path.relative_to(WORKSPACE_DIR).as_posix()}"


def parse_output_paths(brief_text: str) -> list[str]:
    outputs: list[str] = []
    in_block = False
    for raw in brief_text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if stripped == "## Output paths":
            in_block = True
            continue
        if in_block and stripped.startswith("## "):
            break
        if in_block and stripped.startswith("- "):
            outputs.append(stripped[2:].strip().strip("`"))
    return outputs


def normalize_output_paths(task_relpath: str, outputs: list[str]) -> list[str]:
    normalized: list[str] = []
    for output in outputs:
        cleaned = output.strip()
        if not cleaned:
            continue
        if cleaned.startswith("Task reports:") or cleaned.startswith("Reports directory:"):
            continue
        if cleaned.startswith("/"):
            path_obj = Path(cleaned)
            if str(path_obj).startswith(str(WORKSPACE_DIR)):
                normalized.append(rel_to_workspace(path_obj))
                continue
            normalized.append(cleaned)
            continue
        if cleaned.startswith("./tasks/"):
            normalized.append(cleaned)
            continue
        if not re.search(r"(research|reports|scratch|sources|scripts)/", cleaned) and not re.search(
            r"\.(md|json|csv|png|txt)$", cleaned
        ):
            continue
        cleaned = cleaned[2:] if cleaned.startswith("./") else cleaned
        normalized.append(f"{task_relpath}/{cleaned}")
    return normalized


def default_output_paths(task_relpath: str, agent_name: str) -> list[str]:
    slug = agent_name.strip()
    return [
        f"{task_relpath}/research/{slug}.md",
        f"{task_relpath}/research/{slug}.worklog.md",
        f"{task_relpath}/research/{slug}.raw.json",
    ]


def parse_horizon(capsule_text: str) -> str:
    patterns = [
        re.compile(r"horizon:\s*([a-z0-9-]+)", re.IGNORECASE),
        re.compile(r"时间框架[:：]\s*`?([a-z0-9-]+)`?", re.IGNORECASE),
    ]
    for pattern in patterns:
        match = pattern.search(capsule_text)
        if match:
            return match.group(1).strip().lower()
    return "auto"


def backtest_horizons(horizon: str) -> str:
    mapping = {
        "h24-48": "1,2,3",
        "d3-7": "1,2,3,5",
        "w1-2": "3,5,10",
        "w2-4": "5,10,15",
        "m1-3": "5,10,20",
    }
    return mapping.get(horizon, "1,2,3,5")


def wave_for(agent_slug: str) -> int:
    if agent_slug in {"planner", "truth-collector", "universe-builder"}:
        return 0
    if agent_slug == "synthesis-analyst":
        return 2
    if agent_slug == "reviewer":
        return 3
    if agent_slug == "report-generator":
        return 4
    return 1


def build_log_command(
    task_slug: str,
    agent_name: str,
    role: str,
    status: str,
    output_paths: list[str] | None = None,
    note: str = "",
) -> str:
    parts = [
        "python3",
        "./scripts/task_session.py",
        "log-agent",
        "--task-slug",
        task_slug,
        "--agent-name",
        agent_name,
    ]
    if role:
        parts.extend(["--role", role])
    parts.extend(["--status", status])
    for output in output_paths or []:
        parts.extend(["--output-path", output])
    if note:
        parts.extend(["--note", note])
    return " ".join(json.dumps(part, ensure_ascii=False) for part in parts)


def build_spawn_task(prompt_relpath: str, task_relpath: str) -> str:
    return (
        f"Read and execute `{prompt_relpath}` exactly. "
        f"Work only inside `{task_relpath}` and write all findings back into that task directory."
    )


def build_record_spawn_command(coordinator_relpath: str, task_slug: str, agent_name: str) -> str:
    parts = [
        "python3",
        coordinator_relpath,
        "record-spawn",
        "--task-slug",
        task_slug,
        "--agent-name",
        agent_name,
        "--run-id",
        "<RUN_ID>",
        "--child-session-key",
        "<CHILD_SESSION_KEY>",
    ]
    return " ".join(json.dumps(part, ensure_ascii=False) for part in parts)


def build_status_command(coordinator_relpath: str, task_slug: str) -> str:
    parts = [
        "python3",
        coordinator_relpath,
        "status",
        "--task-slug",
        task_slug,
    ]
    return " ".join(json.dumps(part, ensure_ascii=False) for part in parts)


def build_validate_command(coordinator_relpath: str, task_slug: str) -> str:
    parts = [
        "python3",
        coordinator_relpath,
        "validate",
        "--task-slug",
        task_slug,
    ]
    return " ".join(json.dumps(part, ensure_ascii=False) for part in parts)


def build_quant_contract(task_relpath: str, horizon: str) -> str:
    quant_script = f"{task_relpath}/scripts/market-alpha-quant-compass.py"
    runtime_profile = f"{task_relpath}/reports/quant/runtime-profile.json"
    model_router = f"{task_relpath}/reports/quant/model-router.json"
    candidate_csv = f"{task_relpath}/scratch/quant/candidate-factors.csv"
    backtest_csv = f"{task_relpath}/scratch/quant/signal-backtest.csv"
    factor_score = f"{task_relpath}/reports/quant/factor-score.json"
    resonance = f"{task_relpath}/reports/quant/resonance.json"
    backtest_summary = f"{task_relpath}/reports/quant/backtest-summary.json"
    return f"""## Quant Compute Contract

You are running inside the OpenClaw runtime container. If your brief requires numeric validation, use the native `exec` tool and execute the task-local quant chain for real. Do not describe the commands hypothetically.

Always start with runtime detection and model routing:

```bash
python3 {quant_script} detect-runtime --output {runtime_profile}
python3 {quant_script} choose-model --rows 200 --features 6 --horizon {horizon} --target-type continuous --output {model_router}
```

Only claim `score` / `backtest-forward` after checking the inputs are not still template placeholders:

- `candidate-factors.csv` must contain real rows, not just `ticker=EXAMPLE`
- `signal-backtest.csv` must contain a real signal series, not the scaffold sample alone

When the inputs are real, execute:

```bash
python3 {quant_script} score --input {candidate_csv} --factors signal_strength:0.35,relative_strength:0.25,turnover_pulse:0.20,flow_confirmation:0.30,crowding_penalty:-0.30 --top 10 --output {factor_score}
python3 {quant_script} resonance --input {candidate_csv} --factors signal_strength:0.35,relative_strength:0.25,turnover_pulse:0.20,flow_confirmation:0.30,crowding_penalty:-0.30 --top 10 --output {resonance}
python3 {quant_script} backtest-forward --input {backtest_csv} --signal-col signal --horizons {backtest_horizons(horizon)} --output {backtest_summary}
```

If your task-local factor dataset also contains a labeled target such as `forward_return` / `future_return`, run factor mining as well:

```bash
python3 {quant_script} factor-mine --input {candidate_csv} --target forward_return --top 10 --output {task_relpath}/reports/quant/factor-mine.json
```

If the inputs are still template data, do one of the following:

- populate task-local real inputs first and then run the commands above
- or explicitly mark the quant section as blocked due to missing real inputs

Never output fake backtest numbers from template CSVs.
"""


def build_truth_contract(task_relpath: str, task_slug: str) -> str:
    truth_script = f"{task_relpath}/scripts/market-alpha-truth-stack.py"
    truth_ledger = f"{task_relpath}/reports/derivatives/underlying-truth-ledger.json"
    reviewer_verdict = f"{task_relpath}/reports/review/reviewer-verdict.json"
    return f"""## Truth Stack Contract

Use the task-local truth stack instead of keeping spot-truth and reviewer state only in prose.

Artifacts:

- Truth ledger: `{truth_ledger}`
- Reviewer verdict: `{reviewer_verdict}`

Initialize or refresh if needed:

```bash
python3 {truth_script} init-task --task-slug {task_slug}
```

When you confirm current spot truth for a candidate, persist it:

```bash
python3 {truth_script} upsert-underlying --task-slug {task_slug} --symbol <SYMBOL> --price <LAST_PRICE> --as-of <ISO> --source-primary <SOURCE> --source-secondary <SOURCE> --cross-check-diff-pct <PCT> --truth-status VERIFIED|PARTIAL|MISSING --notes '<TEXT>'
```

If you are the reviewer or report owner, you must write a machine-readable verdict before delivery:

```bash
python3 {truth_script} write-reviewer-verdict --task-slug {task_slug} --payload-json '<JSON>'
```

Rules:

- Do not state precise option or execution guidance before the truth ledger exists.
- If no single-name passes, reviewer must record `single_name_status=NO_SINGLE_NAME_PASSED` and explicitly allow degraded ETF-only output.
- Report generation must read the reviewer verdict before finalizing recommendations.
"""


def build_strategy_lab_contract(task_relpath: str, task_slug: str) -> str:
    strategy_script = f"{task_relpath}/scripts/market-alpha-strategy-pool.py"
    registry_preview = f"{task_relpath}/reports/strategy-lab/registry-preview.json"
    factor_library = f"{task_relpath}/reports/strategy-lab/factor-library.json"
    strategy_ranking = f"{task_relpath}/reports/strategy-lab/strategy-ranking.json"
    return f"""## Strategy Lab Contract

When you find a repeatable setup, do not leave it only in markdown. Register it in the task-local strategy lab first.

Artifacts:

- Registry preview: `{registry_preview}`
- Factor library: `{factor_library}`
- Strategy ranking: `{strategy_ranking}`

Initialize or refresh if needed:

```bash
python3 {strategy_script} init-task-lab --task-slug {task_slug} --market multi --style hybrid --horizon auto
python3 {strategy_script} refresh-task-lab --task-slug {task_slug}
```

To stage a repeatable pattern as a strategy candidate:

```bash
python3 {strategy_script} register-candidate --task-slug {task_slug} --strategy-id <ID> --name <NAME> --market <MARKET> --instrument <INSTRUMENT> --style <STYLE> --horizon <HORIZON> --thesis-type <TYPE> --universe-rule '<RULE>' --signal-rule '<RULE>' --factor-list '<CSV>' --regime-tags '<CSV>' --validation-status draft --thesis '<TEXT>'
```

Rules:

- Hunt identifies one-off trades; strategy lab captures repeatable patterns.
- Use `draft` or `incubating` until reviewer explicitly approves promotion.
- Keep factor names and regime tags structured so later pool routing can reuse them.
"""


def build_prompt(
    *,
    task_slug: str,
    task_relpath: str,
    task_capsule_relpath: str,
    skill_brief_relpath: str,
    agent_brief_relpath: str,
    output_paths: list[str],
    agent_name: str,
    role: str,
    mission: str,
    horizon: str,
) -> str:
    worklog_path = next((path for path in output_paths if path.endswith(".worklog.md")), "")
    summary_path = next((path for path in output_paths if path.endswith(".md") and not path.endswith(".worklog.md")), "")
    raw_path = next((path for path in output_paths if path.endswith(".json")), "")
    start_log = build_log_command(
        task_slug=task_slug,
        agent_name=agent_name,
        role=role,
        status="running",
        note="native-subagent started",
    )
    done_log = build_log_command(
        task_slug=task_slug,
        agent_name=agent_name,
        role=role,
        status="completed",
        output_paths=output_paths,
        note="native-subagent completed",
    )
    fail_log = build_log_command(
        task_slug=task_slug,
        agent_name=agent_name,
        role=role,
        status="error",
        output_paths=output_paths,
        note="native-subagent blocked or failed",
    )

    lines = [
        f"# Native Market Alpha Subagent Prompt: {agent_name}",
        "",
        f"- Task dir: `{task_relpath}`",
        f"- Agent brief: `{agent_brief_relpath}`",
        f"- Role: `{role or 'unspecified'}`",
        "",
        "## Execution Mode",
        "",
        "- You are running as an OpenClaw native subagent spawned through `sessions_spawn` / `/subagents`.",
        "- Keep all work inside the task directory. Do not invent a separate runner or scratch area.",
        "- Validate MCP availability from inside the runtime container before depending on it.",
        "- In the current docker-compose, `/mnt/500G-1/Development` is mounted into the gateway container. Entries like `finance-mcp-local` or `tavily-mcp-local` should be file-visible after compose reload; if they still fail, debug server startup or call semantics rather than the volume first.",
        "- Do not invent raw `localhost:3000/mcp/...` routes. Use real tool calls, container-visible paths, or explicit runtime checks.",
        "",
        "## Load Only These Files First",
        "",
        f"1. `{task_capsule_relpath}`",
        f"2. `{skill_brief_relpath}`",
        f"3. `{agent_brief_relpath}`",
        "4. `./SEARCH_RUNTIME.md`",
        "",
        "## Mission",
        "",
        mission,
        "",
        "## Persistence Contract",
        "",
        f"- Final summary path: `{summary_path or '(none specified)'}`",
        f"- Worklog path: `{worklog_path or '(none specified)'}`",
        f"- Structured payload path: `{raw_path or '(none specified)'}`",
        "- Write important findings into the task-local worklog as you confirm them. Do not keep critical research only in the final reply.",
        "- Use structured JSON outputs when the brief asks for machine-readable evidence.",
        "",
        *build_search_runtime_section(path_label="./SEARCH_RUNTIME.md"),
        "",
        "## Output Language",
        "",
        "- Write the final user-facing report in Simplified Chinese by default.",
        "- Only switch to English when the user explicitly requested English.",
        "",
        "## Status Logging",
        "",
        "Run this before substantive work:",
        "",
        "```bash",
        start_log,
        "```",
        "",
        "Run this before your final success reply:",
        "",
        "```bash",
        done_log,
        "```",
        "",
        "If you get blocked or fail, run this first and then start your final answer with `BLOCKED:`:",
        "",
        "```bash",
        fail_log,
        "```",
        "",
        "## Work Rules",
        "",
        f"- Work only under `{task_relpath}`.",
        "- Prefer FinanceMCP first when the needed tool exists. Web search is the fallback, not the default.",
        "- Use the native `subagents` tool only for on-demand status or steering; do not poll in a loop.",
        "- Do not narrate fake progress.",
        "",
        "## Finance Pacing Contract",
        "",
        f"- Start by ensuring the finance ledger exists:",
        "",
        "```bash",
        f"python3 ./scripts/finance-data-budget-guard.py ensure-ledger --task-slug {task_slug}",
        "```",
        "",
        "- Before each Tushare-backed FinanceMCP stock-data request, reserve budget first:",
        "",
        "```bash",
        f"python3 ./scripts/finance-data-budget-guard.py reserve --task-slug {task_slug} --endpoint stock_data --symbol <SYMBOL> --budget-key tushare-stock-data --per-minute 2 --per-day 5 --cooldown-seconds 65 --params-json '<JSON>'",
        "```",
        "",
        "- If reserve returns `FINANCE_BUDGET_WAIT`, wait and retry instead of immediately stampeding into stale fallback data.",
        "- After each live fetch or fallback, append task-local state via:",
        "",
        "```bash",
        f"python3 ./scripts/finance-data-budget-guard.py finalize --task-slug {task_slug} --request-id <REQUEST_ID> --status success|fallback|error --fresh-as-of <ISO>",
        f"python3 ./scripts/finance-data-budget-guard.py set-completeness --task-slug {task_slug} --symbol <SYMBOL> --field <FIELD> --status complete|partial|missing --as-of <ISO> --source <SOURCE>",
        f"python3 ./scripts/finance-data-budget-guard.py upsert-snapshot --task-slug {task_slug} --symbol <SYMBOL> --as-of <ISO> --source <SOURCE> --payload-json '<JSON>'",
        "```",
        "",
        "- `sources/fetch-log.jsonl`, `sources/live-market-snapshot.json`, and `sources/data-completeness.json` are part of the durable audit trail. Keep them updated.",
        "",
        "## News Event Contract",
        "",
        "- For finance-sensitive tasks, persist news and catalysts into the task-local news ledger:",
        "",
        "```bash",
        f"python3 ./scripts/finance-news-event-ledger.py ensure-ledger --task-slug {task_slug}",
        f"python3 ./scripts/finance-news-event-ledger.py append-event --task-slug {task_slug} --headline '<HEADLINE>' --source '<SOURCE>' --symbol '<SYMBOL>' --published-at '<ISO>' --event-type '<EVENT_TYPE>' --driver-type '<DRIVER_TYPE>' --direction-bias '<BULLISH|BEARISH|VOLATILE|MIXED>' --impact-horizon '<HORIZON>' --confidence '<LOW|MEDIUM|HIGH>' --url '<URL>'",
        "```",
        "",
        "- Before synthesis or report generation, summarize these events via:",
        "",
        "```bash",
        f"python3 ./scripts/finance-news-event-ledger.py summary --task-slug {task_slug}",
        "```",
        "",
        "- Final finance reports should include an `## 事件驱动因子` section derived from this ledger, not from memory alone.",
        "",
        "## Timeline Fusion Contract",
        "",
        "- Before final synthesis or report generation, build a task-local timeline/freshness summary:",
        "",
        "```bash",
        f"python3 ./scripts/finance-timeline-fusion.py --task-slug {task_slug} --format markdown --output {task_relpath}/reports/finance-timeline-summary.md",
        "```",
        "",
        "- Use that summary to populate `## Data Freshness & Completeness` rather than guessing freshness manually.",
        "- If `Mixed freshness risk != LOW` or `Timeline integrity != COHERENT`, do not emit `Precision level: EXECUTABLE`.",
        "",
    ]

    lowered_agent_context = f"{agent_name} {role} {mission}".lower()

    if agent_name == "quant-verifier" or "quant" in (role or "").lower() or "quant" in mission.lower():
        lines.extend([build_quant_contract(task_relpath, horizon), ""])
    else:
        lines.extend(
            [
                "## Quant Reuse Rule",
                "",
                "- If you need an existing numeric check, reuse task-local `reports/quant/*` and `scratch/quant/*` outputs before inventing numbers.",
                "- If new computation is required, coordinate through the task-local `scripts/market-alpha-quant-compass.py` chain.",
                "",
            ]
        )

    if any(token in lowered_agent_context for token in ["truth", "review", "report-generator", "single-name", "universe-builder"]):
        lines.extend([build_truth_contract(task_relpath, task_slug), ""])

    if any(token in lowered_agent_context for token in ["strategy", "single-name", "synthesis", "quant", "review"]):
        lines.extend([build_strategy_lab_contract(task_relpath, task_slug), ""])

    lines.extend(
        [
            "## Final Reply Contract",
            "",
            "- Return the substantive result directly as markdown.",
            "- If blocked, start with `BLOCKED:` and keep the blocker concrete.",
            "- The final reply should summarize the task-local outputs, not replace them.",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare native OpenClaw subagent prompt pack for market-alpha tasks")
    parser.add_argument("--task-slug")
    parser.add_argument("--require-briefs", action="store_true")
    args = parser.parse_args()

    task_dir = task_session.resolve_task_dir(task_slug=args.task_slug, prefer_active=True)
    agents_dir = task_dir / "agents"
    briefs = sorted(agents_dir.glob("*.md")) if agents_dir.exists() else []
    if not briefs:
        marker = "MARKET_ALPHA_NATIVE_SUBAGENTS_ERROR" if args.require_briefs else "MARKET_ALPHA_NATIVE_SUBAGENTS_SKIP"
        print(marker)
        print(f"TASK_DIR={task_dir}")
        print("REASON=no agent briefs found")
        return 1 if args.require_briefs else 0

    native_dir = task_dir / "native-subagents"
    prompts_dir = native_dir / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    task_relpath = rel_to_workspace(task_dir)
    coordinator_relpath = rel_to_workspace(SCRIPT_DIR / "market-alpha-native-coordinator.py")
    capsule_path = task_dir / "capsules" / "task-capsule.md"
    skill_brief_path = task_dir / "capsules" / "skill-brief.md"
    task_capsule_relpath = rel_to_workspace(capsule_path)
    skill_brief_relpath = rel_to_workspace(skill_brief_path)
    capsule_text = capsule_path.read_text(encoding="utf-8") if capsule_path.exists() else ""
    horizon = parse_horizon(capsule_text)
    task_slug = task_dir.name.split("-", 3)[-1] if "-" in task_dir.name else task_dir.name

    rows = read_jsonl(task_dir / "agents.jsonl")
    latest_by_agent: dict[str, dict[str, Any]] = {}
    for row in rows:
        name = str(row.get("agent_name", "")).strip()
        if name:
            latest_by_agent[name] = row

    manifest_agents: list[dict[str, Any]] = []
    waves: dict[int, list[str]] = defaultdict(list)
    for brief in briefs:
        agent_name = brief.stem
        row = latest_by_agent.get(agent_name, {})
        brief_text = brief.read_text(encoding="utf-8")
        output_paths = [path for path in (row.get("output_paths") or []) if isinstance(path, str)]
        if not output_paths:
            output_paths = parse_output_paths(brief_text)
        output_paths = normalize_output_paths(task_relpath, output_paths)
        if not output_paths:
            output_paths = default_output_paths(task_relpath, agent_name)
        prompt_path = prompts_dir / brief.name
        prompt_relpath = rel_to_workspace(prompt_path)
        agent_brief_relpath = rel_to_workspace(brief)
        role = str(row.get("role", "")).strip()
        mission = str(row.get("mission", "")).strip() or "Return a concise result tied to the task capsule."
        wave = wave_for(agent_name)
        waves[wave].append(agent_name)

        prompt_text = build_prompt(
            task_slug=task_slug,
            task_relpath=task_relpath,
            task_capsule_relpath=task_capsule_relpath,
            skill_brief_relpath=skill_brief_relpath,
            agent_brief_relpath=agent_brief_relpath,
            output_paths=output_paths,
            agent_name=agent_name,
            role=role,
            mission=mission,
            horizon=horizon,
        )
        write_text(prompt_path, prompt_text)

        manifest_agents.append(
            OrderedDict(
                agent_name=agent_name,
                role=role,
                wave=wave,
                parallel_group=str(row.get("parallel_group", "")).strip(),
                brief_path=agent_brief_relpath,
                prompt_path=prompt_relpath,
                spawn_label=f"market-alpha:{agent_name}",
                spawn_task=build_spawn_task(prompt_relpath, task_relpath),
                spawn_payload=OrderedDict(
                    label=f"market-alpha:{agent_name}",
                    task=build_spawn_task(prompt_relpath, task_relpath),
                    runTimeoutSeconds=900,
                    cleanup="keep",
                ),
                record_spawn_command=build_record_spawn_command(coordinator_relpath, task_slug, agent_name),
                output_paths=output_paths,
            )
        )

    playbook_path = native_dir / "coordinator-playbook.md"
    write_text(
        playbook_path,
        "\n".join(
            [
                "# Native Market Alpha Coordinator Playbook",
                "",
                f"- Task dir: `{task_relpath}`",
                "- Main path: OpenClaw native `sessions_spawn` / `/subagents`.",
                "- Legacy `market-alpha-run-batch.sh` is fallback only. Do not use it as the default path.",
                "- FinanceMCP host-mounted entry paths are normal here. Do not downgrade because the path starts with `/mnt/500G-1/...`; verify tool/runtime failure first.",
                "",
                "## Spawn Waves",
                "",
                *[
                    f"- Wave {wave}: {', '.join(sorted(names))}"
                    for wave, names in sorted(waves.items())
                ],
                "",
                "## Spawn Pattern",
                "",
                "Run this preflight first:",
                "",
                "```bash",
                build_validate_command(coordinator_relpath, task_slug),
                "```",
                "",
                "For each agent in the current wave, call `sessions_spawn` with the exact `spawn_payload` object from `manifest.json`:",
                "",
                "- Do not reconstruct the payload from memory when `manifest.json` already has it.",
                "- A wave is not considered started until `sessions_spawn` returns `status=\"accepted\"` with a `runId` and `childSessionKey`.",
                "- After each accepted spawn, persist the receipt immediately with that agent's `record_spawn_command`, replacing `<RUN_ID>` and `<CHILD_SESSION_KEY>`.",
                "- If `sessions_spawn` is unavailable in the live tool list, stop and say `BLOCKED:` instead of pretending the wave has started.",
                "",
                "Start the next wave only after the current wave has either produced task-local outputs or been explicitly reviewed for blockers.",
                "",
                "## Observability",
                "",
                "- Before reporting progress, run the task-local status snapshot:",
                "",
                "```bash",
                build_status_command(coordinator_relpath, task_slug),
                "```",
                "",
                "- Use `subagents(action=list)` for a quick live inventory.",
                "- Use `subagents(action=info|log)` only on demand, not in a polling loop.",
                "- Task-local `agents.jsonl`, `research/*.worklog.md`, and `reports/quant/*` are the durable audit trail. Do not claim a wave completed unless these files say so.",
                "",
                "## Quant Rule",
                "",
                "- `quant-verifier` must execute the task-local `market-alpha-quant-compass.py` chain inside the OpenClaw runtime container.",
                "- If quant inputs are still placeholder templates, the agent must either fill real inputs first or explicitly mark the quant section blocked.",
                "",
                "## Delivery Rule",
                "",
                "- Spawn `report-generator` only after synthesis and review are complete enough to produce a delivery candidate.",
                "- Final delivery still goes through `market-alpha-deliver.sh` so the report gate can enforce `Quant Evidence` and `TASK_PATH`.",
            ]
        ),
    )

    manifest_path = native_dir / "manifest.json"
    manifest = OrderedDict(
        task_slug=task_dir.name.split("-", 3)[-1] if "-" in task_dir.name else task_dir.name,
        task_path=task_relpath,
        created_at_utc=task_session.iso_now(),
        runtime="openclaw-native-subagents",
        horizon=horizon,
        coordinator_script=coordinator_relpath,
        validate_command=build_validate_command(coordinator_relpath, task_slug),
        status_command=build_status_command(coordinator_relpath, task_slug),
        waves=OrderedDict((str(wave), sorted(names)) for wave, names in sorted(waves.items())),
        agents=manifest_agents,
        playbook_path=rel_to_workspace(playbook_path),
    )
    write_text(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2))

    readme_path = native_dir / "README.md"
    write_text(
        readme_path,
        "\n".join(
            [
                "# Native Market Alpha Subagents",
                "",
                f"- Manifest: `{rel_to_workspace(manifest_path)}`",
                f"- Coordinator playbook: `{rel_to_workspace(playbook_path)}`",
                f"- Coordinator bridge: `{coordinator_relpath}`",
                "- Prompts: `prompts/*.md`",
                "",
                "These files are generated for the main market-alpha coordinator agent.",
                "Use them with OpenClaw native `sessions_spawn` / `/subagents`, not with the legacy external runner.",
            ]
        ),
    )

    print("MARKET_ALPHA_NATIVE_SUBAGENTS_OK")
    print(f"TASK_DIR={task_dir}")
    print(f"MANIFEST={manifest_path}")
    print(f"PLAYBOOK={playbook_path}")
    print(f"PROMPT_COUNT={len(manifest_agents)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
