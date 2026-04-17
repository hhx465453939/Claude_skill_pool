#!/usr/bin/env python3

from __future__ import annotations

import argparse
from collections import OrderedDict
from pathlib import Path

from _short_alpha_common import read_json, resolve_output, ensure_task_dir, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an OODA loop summary from short-alpha-general outputs")
    parser.add_argument("--task-slug")
    parser.add_argument("--regime-input", required=True)
    parser.add_argument("--event-clock-input", required=True)
    parser.add_argument("--fertility-input", required=True)
    parser.add_argument("--execution-input", required=True)
    parser.add_argument("--review-input", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    task_dir = ensure_task_dir(args.task_slug) if args.task_slug else None
    regime = read_json(Path(args.regime_input), {})
    event_clock = read_json(Path(args.event_clock_input), {})
    fertility = read_json(Path(args.fertility_input), {})
    execution = read_json(Path(args.execution_input), {})
    review = read_json(Path(args.review_input), {})

    fertile = [row.get("ticker") for row in fertility.get("opportunities", []) if row.get("fertility_status") == "fertile"]
    deserts = [row.get("ticker") for row in fertility.get("opportunities", []) if row.get("fertility_status") == "desert"]
    strike_ready = execution.get("strike_ready", [])
    probe = execution.get("probe", [])
    watchlist = execution.get("watchlist", [])
    forbidden = execution.get("forbidden", [])

    if strike_ready:
        tempo = "strike-fast"
        command_intent = "Exploit the active window immediately and size by tier."
    elif probe:
        tempo = "probe-and-confirm"
        command_intent = "Deploy light capital, confirm reaction, then scale only on validation."
    elif watchlist:
        tempo = "observe-and-wait"
        command_intent = "Do not force deployment. Preserve capital until timing and truth align."
    else:
        tempo = "stand-down"
        command_intent = "No fertile battlefield exists. Do not deploy."

    payload = OrderedDict(
        tool="short-alpha-general/ooda-loop",
        observe=OrderedDict(
            regime=regime.get("regime", ""),
            event_count=len(event_clock.get("events", [])),
            truth_ready_count=len([row for row in execution.get("rows", []) if row.get("truth_status") == "VERIFIED"]),
        ),
        orient=OrderedDict(
            primary_battlefield=next((tier for tier in ["B", "C", "A"] if tier in [row.get("deployment_tier") for row in execution.get("rows", []) if row.get("status") in {"strike-ready", "probe", "watchlist"}]), "D"),
            fertile_candidates=fertile,
            deserts=deserts,
        ),
        decide=OrderedDict(
            strike_ready=strike_ready,
            probe=probe,
            watchlist=watchlist,
            forbidden=forbidden,
            reviewer_status=review.get("status", "UNKNOWN"),
        ),
        act=OrderedDict(
            tempo=tempo,
            command_intent=command_intent,
            allowed_output=review.get("allowed_output", "UNKNOWN"),
        ),
    )
    output_path = resolve_output(args.output, task_dir, "results/ooda/ooda-loop.json")
    write_json(output_path, payload)
    print("SHORT_ALPHA_OODA_LOOP_OK")
    print(f"OUTPUT={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
