#!/usr/bin/env python3

from __future__ import annotations

import argparse
from collections import OrderedDict, defaultdict
from pathlib import Path
import statistics

from _short_alpha_common import ensure_task_dir, read_json, write_json


def avg(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(statistics.mean(values))


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a short-alpha-general score calibration summary")
    parser.add_argument("--task-slug", required=True)
    parser.add_argument("--campaign-input", required=True)
    parser.add_argument("--execution-input", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    task_dir = ensure_task_dir(args.task_slug)
    campaign = read_json(Path(args.campaign_input), {})
    execution = read_json(Path(args.execution_input), {})

    scores_by_status: dict[str, list[float]] = defaultdict(list)
    scores_by_tier: dict[str, list[float]] = defaultdict(list)
    for row in execution.get("rows", []):
        score = float(row.get("campaign_score", 0.0) or 0.0)
        scores_by_status[str(row.get("status", "unknown"))].append(score)
        scores_by_tier[str(row.get("deployment_tier", "unknown"))].append(score)

    payload = OrderedDict(
        tool="short-alpha-general/score-calibration",
        task_dir=str(task_dir),
        status_bands=OrderedDict(
            (
                status,
                OrderedDict(
                    count=len(values),
                    avg_campaign_score=round(avg(values), 4),
                    min_campaign_score=round(min(values), 4) if values else 0.0,
                    max_campaign_score=round(max(values), 4) if values else 0.0,
                ),
            )
            for status, values in sorted(scores_by_status.items())
        ),
        tier_bands=OrderedDict(
            (
                tier,
                OrderedDict(
                    count=len(values),
                    avg_campaign_score=round(avg(values), 4),
                    min_campaign_score=round(min(values), 4) if values else 0.0,
                    max_campaign_score=round(max(values), 4) if values else 0.0,
                ),
            )
            for tier, values in sorted(scores_by_tier.items())
        ),
        threshold_hints=OrderedDict(
            strike_ready_min=round(min(scores_by_status.get("strike-ready", [0.72])), 4),
            probe_min=round(min(scores_by_status.get("probe", [0.55])), 4),
            watchlist_min=round(min(scores_by_status.get("watchlist", [0.40])), 4),
        ),
    )

    output_path = Path(args.output) if args.output else task_dir / "reports" / "short-alpha-general" / "score-calibration.json"
    write_json(output_path, payload)
    calibration_root = task_dir.parent.parent / "strategy-pool" / "calibration"
    calibration_root.mkdir(parents=True, exist_ok=True)
    write_json(calibration_root / f"{task_dir.name}-short-alpha-general-calibration.json", payload)
    print("SHORT_ALPHA_SCORE_CALIBRATION_OK")
    print(f"OUTPUT={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
