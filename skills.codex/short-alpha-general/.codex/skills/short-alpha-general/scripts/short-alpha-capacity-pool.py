#!/usr/bin/env python3

from __future__ import annotations

import argparse
from collections import OrderedDict, defaultdict
from pathlib import Path

from _short_alpha_common import read_json, resolve_output, ensure_task_dir, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a capacity-gradient deployment pool from campaign and execution outputs")
    parser.add_argument("--task-slug")
    parser.add_argument("--campaign-input", required=True)
    parser.add_argument("--execution-input", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    task_dir = ensure_task_dir(args.task_slug) if args.task_slug else None
    campaign = read_json(Path(args.campaign_input), {})
    execution = read_json(Path(args.execution_input), {})

    campaign_rows = {str(row.get("ticker", "")).upper(): row for row in campaign.get("rows", []) if str(row.get("ticker", "")).strip()}
    rows = []
    tier_map: dict[str, list[dict]] = defaultdict(list)
    action_map: dict[str, list[dict]] = defaultdict(list)

    for exec_row in execution.get("rows", []):
        ticker = str(exec_row.get("ticker", "")).strip().upper()
        if not ticker:
            continue
        campaign_row = campaign_rows.get(ticker, {})
        merged = OrderedDict(
            ticker=ticker,
            deployment_tier=str(exec_row.get("deployment_tier", "D")),
            status=str(exec_row.get("status", "forbidden")),
            campaign_score=float(exec_row.get("campaign_score", 0.0) or 0.0),
            dao_alignment=float(exec_row.get("dao_alignment", 0.0) or 0.0),
            timing_quality=float(exec_row.get("timing_quality", 0.0) or 0.0),
            fertility_score=float(exec_row.get("fertility_score", 0.0) or 0.0),
            capacity_score=float(campaign_row.get("capacity_score", 0.0) or 0.0),
            crowding_score=float(campaign_row.get("crowding_score", 0.0) or 0.0),
            action_window=str(campaign_row.get("action_window", "")),
            rationale=str(exec_row.get("rationale", "")),
        )
        rows.append(merged)
        tier_map[merged["deployment_tier"]].append(merged)
        action_map[merged["status"]].append(merged)

    ordered_tiers = OrderedDict((tier, tier_map.get(tier, [])) for tier in ["A", "B", "C", "D"])
    ordered_actions = OrderedDict((label, action_map.get(label, [])) for label in ["strike-ready", "probe", "watchlist", "forbidden"])
    payload = OrderedDict(
        tool="short-alpha-general/capacity-pool",
        rows=rows,
        tiers=ordered_tiers,
        actions=ordered_actions,
    )
    output_path = resolve_output(args.output, task_dir, "results/execution/deployment-pool.json")
    write_json(output_path, payload)
    print("SHORT_ALPHA_CAPACITY_POOL_OK")
    print(f"OUTPUT={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
