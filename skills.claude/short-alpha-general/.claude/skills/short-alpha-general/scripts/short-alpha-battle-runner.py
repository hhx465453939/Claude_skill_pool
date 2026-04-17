#!/usr/bin/env python3

from __future__ import annotations

import argparse
import shutil
import subprocess
from collections import OrderedDict
from pathlib import Path

from _short_alpha_common import ensure_task_dir, read_json, write_json


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def maybe_copy(src: Path, dst: Path) -> None:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def sync_latest_scripts(task_dir: Path) -> None:
    source_dir = Path(__file__).resolve().parent
    target_dir = task_dir / "scripts"
    target_dir.mkdir(parents=True, exist_ok=True)
    for pattern in ("*.py", "*.sh"):
        for src in source_dir.glob(pattern):
            if not src.is_file():
                continue
            dst = target_dir / src.name
            shutil.copy2(src, dst)
            try:
                dst.chmod(0o755)
            except Exception:
                pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the full short-alpha-general battle pipeline inside an existing task")
    parser.add_argument("--task-slug", required=True)
    parser.add_argument("--raw-candidates")
    parser.add_argument("--news-log")
    parser.add_argument("--truth-ledger")
    parser.add_argument("--degrade-reason", default="")
    parser.add_argument("--report-name", default="REPORT.md")
    args = parser.parse_args()

    task_dir = ensure_task_dir(args.task_slug)
    sync_latest_scripts(task_dir)
    scripts_dir = task_dir / "scripts"
    report_root = task_dir / args.report_name

    raw_candidates = Path(args.raw_candidates) if args.raw_candidates else task_dir / "results" / "candidates" / "candidates.json"
    news_log = Path(args.news_log) if args.news_log else task_dir / "sources" / "news-event-log.jsonl"
    truth_ledger = Path(args.truth_ledger) if args.truth_ledger else task_dir / "reports" / "derivatives" / "underlying-truth-ledger.json"
    task_raw_candidates = task_dir / "results" / "candidates" / "candidates.json"
    task_news_log = task_dir / "sources" / "news-event-log.jsonl"
    task_truth_ledger = task_dir / "reports" / "derivatives" / "underlying-truth-ledger.json"

    if args.degrade_reason:
        run(["python3", str(scripts_dir / "short-alpha-runtime-guard.py"), "parent-only", "--task-slug", args.task_slug, "--reason", args.degrade_reason])
    else:
        run(["python3", str(scripts_dir / "short-alpha-runtime-guard.py"), "status", "--task-slug", args.task_slug])

    if not raw_candidates.exists():
        raise SystemExit(f"missing raw candidates input: {raw_candidates}")
    maybe_copy(raw_candidates, task_raw_candidates)
    if news_log.exists():
        maybe_copy(news_log, task_news_log)
    else:
        task_news_log.parent.mkdir(parents=True, exist_ok=True)
        task_news_log.write_text("", encoding="utf-8")
    if truth_ledger.exists():
        maybe_copy(truth_ledger, task_truth_ledger)
    else:
        task_truth_ledger.parent.mkdir(parents=True, exist_ok=True)
        write_json(task_truth_ledger, {"symbols": []})

    run(["python3", str(scripts_dir / "short-alpha-market-observe.py"), "--task-slug", args.task_slug, "--raw-candidates", str(task_raw_candidates), "--news-log", str(task_news_log)])
    run(["python3", str(scripts_dir / "short-alpha-regime-engine.py"), "--task-slug", args.task_slug])
    run(["python3", str(scripts_dir / "short-alpha-event-clock.py"), "--task-slug", args.task_slug])
    run(["python3", str(scripts_dir / "short-alpha-terrain-engine.py"), "--task-slug", args.task_slug, "--candidates-input", str(task_dir / "results" / "candidates" / "candidates-enriched.json")])
    run([
        "python3",
        str(scripts_dir / "short-alpha-fertility-engine.py"),
        "--task-slug",
        args.task_slug,
        "--candidates-input",
        str(task_dir / "results" / "candidates" / "candidates-enriched.json"),
        "--terrain-input",
        str(task_dir / "results" / "terrain" / "terrain-map.json"),
        "--event-clock-input",
        str(task_dir / "results" / "event-clock" / "trigger-watchlist.json"),
    ])
    run([
        "python3",
        str(scripts_dir / "short-alpha-campaign-score.py"),
        "--task-slug",
        args.task_slug,
        "--candidates-input",
        str(task_dir / "results" / "candidates" / "candidates-enriched.json"),
        "--regime-input",
        str(task_dir / "results" / "regime" / "regime-snapshot.json"),
        "--terrain-input",
        str(task_dir / "results" / "terrain" / "terrain-map.json"),
        "--fertility-input",
        str(task_dir / "results" / "terrain" / "fertility-map.json"),
        "--event-clock-input",
        str(task_dir / "results" / "event-clock" / "trigger-watchlist.json"),
    ])
    run([
        "python3",
        str(scripts_dir / "short-alpha-execution-governor.py"),
        "--task-slug",
        args.task_slug,
        "--campaign-input",
        str(task_dir / "results" / "campaign" / "campaign-score.json"),
        "--truth-ledger-input",
        str(task_truth_ledger),
    ])
    run([
        "python3",
        str(scripts_dir / "short-alpha-capacity-pool.py"),
        "--task-slug",
        args.task_slug,
        "--campaign-input",
        str(task_dir / "results" / "campaign" / "campaign-score.json"),
        "--execution-input",
        str(task_dir / "results" / "execution" / "setup-quality.json"),
    ])
    run([
        "python3",
        str(scripts_dir / "short-alpha-review-gate.py"),
        "--task-slug",
        args.task_slug,
        "--regime-input",
        str(task_dir / "results" / "regime" / "regime-snapshot.json"),
        "--campaign-input",
        str(task_dir / "results" / "campaign" / "campaign-score.json"),
        "--execution-input",
        str(task_dir / "results" / "execution" / "setup-quality.json"),
    ])
    run([
        "python3",
        str(scripts_dir / "short-alpha-ooda-loop.py"),
        "--task-slug",
        args.task_slug,
        "--regime-input",
        str(task_dir / "results" / "regime" / "regime-snapshot.json"),
        "--event-clock-input",
        str(task_dir / "results" / "event-clock" / "catalyst-timeline.json"),
        "--fertility-input",
        str(task_dir / "results" / "terrain" / "fertility-map.json"),
        "--execution-input",
        str(task_dir / "results" / "execution" / "setup-quality.json"),
        "--review-input",
        str(task_dir / "reports" / "review" / "reviewer-verdict.json"),
    ])
    run([
        "python3",
        str(scripts_dir / "short-alpha-strategy-register.py"),
        "--task-slug",
        args.task_slug,
        "--campaign-input",
        str(task_dir / "results" / "campaign" / "campaign-score.json"),
        "--execution-input",
        str(task_dir / "results" / "execution" / "setup-quality.json"),
        "--review-input",
        str(task_dir / "reports" / "review" / "reviewer-verdict.json"),
    ])
    run([
        "python3",
        str(scripts_dir / "short-alpha-score-calibration.py"),
        "--task-slug",
        args.task_slug,
        "--campaign-input",
        str(task_dir / "results" / "campaign" / "campaign-score.json"),
        "--execution-input",
        str(task_dir / "results" / "execution" / "setup-quality.json"),
    ])
    run(["python3", str(scripts_dir / "short-alpha-report-packager.py"), "--task-slug", args.task_slug])

    command_brief = task_dir / "reports" / "short-alpha-general" / "command-brief.md"
    maybe_copy(command_brief, report_root)

    reviewer = read_json(task_dir / "reports" / "review" / "reviewer-verdict.json", {})
    payload = OrderedDict(
        tool="short-alpha-general/battle-runner",
        task_dir=str(task_dir),
        report=str(report_root),
        reviewer_status=reviewer.get("status", "UNKNOWN"),
        allowed_output=reviewer.get("allowed_output", "UNKNOWN"),
    )
    write_json(task_dir / "reports" / "short-alpha-general" / "battle-runner-summary.json", payload)
    print("SHORT_ALPHA_BATTLE_RUNNER_OK")
    print(f"TASK_DIR={task_dir}")
    print(f"REPORT={report_root}")
    print(f"REVIEWER_STATUS={payload['reviewer_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
