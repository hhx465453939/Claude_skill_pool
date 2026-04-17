#!/usr/bin/env python3

from __future__ import annotations

import argparse
from collections import OrderedDict
from pathlib import Path

from _short_alpha_common import clamp, normalize_ticker, read_rows, resolve_output, ensure_task_dir, to_float, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute crowding/capacity terrain for short-horizon candidates")
    parser.add_argument("--task-slug")
    parser.add_argument("--candidates-input", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    task_dir = ensure_task_dir(args.task_slug) if args.task_slug else None
    rows = read_rows(Path(args.candidates_input))
    terrain_rows = []
    max_adv = max([to_float(row.get("avg_dollar_volume_m"), 0.0) or 0.0 for row in rows] + [1.0])
    max_mcap = max([to_float(row.get("market_cap_b"), 0.0) or 0.0 for row in rows] + [1.0])

    for row in rows:
        ticker = normalize_ticker(row.get("ticker"))
        if not ticker:
            continue
        adv = to_float(row.get("avg_dollar_volume_m"), 0.0) or 0.0
        mcap = to_float(row.get("market_cap_b"), 0.0) or 0.0
        attention = to_float(row.get("attention_level"), 0.35) or 0.35
        rel_strength = to_float(row.get("relative_strength"), 0.45) or 0.45
        crowding = to_float(row.get("crowding_score"), None)
        if crowding is None:
            crowding = clamp(attention * 0.65 + rel_strength * 0.35)
        capacity = clamp((adv / max_adv) * 0.65 + (mcap / max_mcap) * 0.35)
        terrain_quality = clamp(capacity * 0.55 + (1.0 - crowding) * 0.45)
        terrain_rows.append(
            OrderedDict(
                ticker=ticker,
                crowding_score=round(crowding, 4),
                capacity_score=round(capacity, 4),
                terrain_quality=round(terrain_quality, 4),
                avg_dollar_volume_m=adv,
                market_cap_b=mcap,
            )
        )

    payload = OrderedDict(tool="short-alpha-general/terrain-engine", candidates=terrain_rows)
    output_path = resolve_output(args.output, task_dir, "results/terrain/terrain-map.json")
    write_json(output_path, payload)
    print("SHORT_ALPHA_TERRAIN_ENGINE_OK")
    print(f"OUTPUT={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
