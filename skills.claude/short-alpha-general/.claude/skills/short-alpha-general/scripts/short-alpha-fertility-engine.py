#!/usr/bin/env python3

from __future__ import annotations

import argparse
from collections import OrderedDict
from pathlib import Path

from _short_alpha_common import clamp, normalize_ticker, read_json, read_rows, resolve_output, ensure_task_dir, to_float, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify fertile vs barren opportunity terrain")
    parser.add_argument("--task-slug")
    parser.add_argument("--candidates-input", required=True)
    parser.add_argument("--terrain-input", required=True)
    parser.add_argument("--event-clock-input", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    task_dir = ensure_task_dir(args.task_slug) if args.task_slug else None
    candidates = {normalize_ticker(row.get("ticker")): row for row in read_rows(Path(args.candidates_input)) if normalize_ticker(row.get("ticker"))}
    terrain = {normalize_ticker(row.get("ticker")): row for row in read_json(Path(args.terrain_input), {}).get("candidates", []) if normalize_ticker(row.get("ticker"))}
    event_watch = {normalize_ticker(row.get("ticker")): row for row in read_json(Path(args.event_clock_input), {}).get("watchlist", []) if normalize_ticker(row.get("ticker"))}

    results = []
    for ticker, row in sorted(candidates.items()):
        terrain_row = terrain.get(ticker, {})
        event_row = event_watch.get(ticker, {})
        evidence_edge = to_float(row.get("evidence_edge"), 0.45) or 0.45
        hidden_catalyst_score = to_float(row.get("hidden_catalyst_score"), 0.45) or 0.45
        attention_gap = to_float(row.get("attention_gap"), 0.25) or 0.25
        capacity_score = to_float(terrain_row.get("capacity_score"), 0.20) or 0.20
        event_quality = to_float(event_row.get("top_event_quality"), 0.35) or 0.35
        fertility = clamp(
            evidence_edge * 0.25
            + hidden_catalyst_score * 0.20
            + attention_gap * 0.20
            + event_quality * 0.20
            + capacity_score * 0.15
        )
        if fertility >= 0.62 and event_quality >= 0.52 and attention_gap >= 0.25:
            status = "fertile"
            desert_penalty = 0.0
        elif fertility >= 0.45:
            status = "borderline"
            desert_penalty = 0.10
        else:
            status = "desert"
            desert_penalty = 0.35
        results.append(
            OrderedDict(
                ticker=ticker,
                fertility_score=round(fertility, 4),
                fertility_status=status,
                desert_penalty=round(desert_penalty, 4),
                event_quality=round(event_quality, 4),
                attention_gap=round(attention_gap, 4),
                evidence_edge=round(evidence_edge, 4),
            )
        )

    payload = OrderedDict(tool="short-alpha-general/fertility-engine", opportunities=results)
    output_path = resolve_output(args.output, task_dir, "results/terrain/fertility-map.json")
    write_json(output_path, payload)
    print("SHORT_ALPHA_FERTILITY_ENGINE_OK")
    print(f"OUTPUT={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
