#!/usr/bin/env python3

from __future__ import annotations

import argparse
from collections import OrderedDict
from pathlib import Path

from _short_alpha_common import clamp, normalize_ticker, read_json, read_rows, resolve_output, ensure_task_dir, score_to_tier, to_float, write_json


def dao_alignment_for_row(row: dict, regime: dict) -> float:
    river = str(row.get("strategic_river", "")).strip()
    allowed = set(regime.get("allowed_strategic_rivers", []))
    forbidden = set(regime.get("forbidden_strategic_rivers", []))
    if river in forbidden:
        return 0.20
    if river in allowed:
        return 0.85
    return 0.55


def main() -> int:
    parser = argparse.ArgumentParser(description="Score short-horizon campaigns under dao-tian-di-jiang-fa")
    parser.add_argument("--task-slug")
    parser.add_argument("--candidates-input", required=True)
    parser.add_argument("--regime-input", required=True)
    parser.add_argument("--terrain-input", required=True)
    parser.add_argument("--fertility-input", required=True)
    parser.add_argument("--event-clock-input", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    task_dir = ensure_task_dir(args.task_slug) if args.task_slug else None
    candidates = {normalize_ticker(row.get("ticker")): row for row in read_rows(Path(args.candidates_input)) if normalize_ticker(row.get("ticker"))}
    regime = read_json(Path(args.regime_input), {})
    terrain = {normalize_ticker(row.get("ticker")): row for row in read_json(Path(args.terrain_input), {}).get("candidates", []) if normalize_ticker(row.get("ticker"))}
    fertility = {normalize_ticker(row.get("ticker")): row for row in read_json(Path(args.fertility_input), {}).get("opportunities", []) if normalize_ticker(row.get("ticker"))}
    event_clock = {normalize_ticker(row.get("ticker")): row for row in read_json(Path(args.event_clock_input), {}).get("watchlist", []) if normalize_ticker(row.get("ticker"))}

    rows = []
    for ticker, row in sorted(candidates.items()):
        terrain_row = terrain.get(ticker, {})
        fert_row = fertility.get(ticker, {})
        event_row = event_clock.get(ticker, {})
        dao_alignment = dao_alignment_for_row(row, regime)
        timing_quality = to_float(event_row.get("top_event_quality"), 0.35) or 0.35
        terrain_quality = to_float(terrain_row.get("terrain_quality"), 0.30) or 0.30
        fertility_score = to_float(fert_row.get("fertility_score"), 0.35) or 0.35
        crowding_penalty = (to_float(terrain_row.get("crowding_score"), 0.50) or 0.50) * 0.10
        desert_penalty = to_float(fert_row.get("desert_penalty"), 0.20) or 0.20
        evidence_edge = to_float(row.get("evidence_edge"), 0.45) or 0.45
        attention_imminence = clamp((timing_quality + (to_float(row.get("attention_gap"), 0.2) or 0.2)) / 2.0)
        execution_friction = 0.05 if (to_float(terrain_row.get("capacity_score"), 0.2) or 0.2) < 0.20 else 0.0
        campaign_score = clamp(
            dao_alignment * 0.18
            + timing_quality * 0.19
            + terrain_quality * 0.15
            + evidence_edge * 0.15
            + attention_imminence * 0.12
            + fertility_score * 0.15
            - crowding_penalty
            - desert_penalty
            - execution_friction
        )
        capacity_score = to_float(terrain_row.get("capacity_score"), 0.20) or 0.20
        deployment_tier = score_to_tier(capacity_score, to_float(terrain_row.get("crowding_score"), 0.5) or 0.5, fertility_score)
        rows.append(
            OrderedDict(
                ticker=ticker,
                campaign_score=round(campaign_score, 4),
                dao_alignment=round(dao_alignment, 4),
                timing_quality=round(timing_quality, 4),
                terrain_quality=round(terrain_quality, 4),
                evidence_edge=round(evidence_edge, 4),
                attention_imminence=round(attention_imminence, 4),
                fertility_score=round(fertility_score, 4),
                capacity_score=round(capacity_score, 4),
                crowding_score=round(to_float(terrain_row.get("crowding_score"), 0.5) or 0.5, 4),
                desert_penalty=round(desert_penalty, 4),
                deployment_tier=deployment_tier,
                action_window=str(event_row.get("action_window", "watch")),
            )
        )

    rows.sort(key=lambda item: item["campaign_score"], reverse=True)
    payload = OrderedDict(
        tool="short-alpha-general/campaign-score",
        market=regime.get("market", ""),
        horizon=regime.get("horizon", ""),
        rows=rows,
    )
    output_path = resolve_output(args.output, task_dir, "results/campaign/campaign-score.json")
    write_json(output_path, payload)
    print("SHORT_ALPHA_CAMPAIGN_SCORE_OK")
    print(f"OUTPUT={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
