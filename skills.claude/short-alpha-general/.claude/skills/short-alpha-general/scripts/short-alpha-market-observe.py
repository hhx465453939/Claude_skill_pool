#!/usr/bin/env python3

from __future__ import annotations

import argparse
from collections import OrderedDict
from pathlib import Path

from _short_alpha_common import clamp, normalize_text, normalize_ticker, read_json, read_jsonl, resolve_output, ensure_task_dir, to_float, write_json


MARKET_PRIORS = {
    "AMZN": {"market_cap_b": 1900, "avg_dollar_volume_m": 12000, "attention_level": 0.82, "relative_strength": 0.72},
    "META": {"market_cap_b": 1350, "avg_dollar_volume_m": 11000, "attention_level": 0.80, "relative_strength": 0.70},
    "JPM": {"market_cap_b": 540, "avg_dollar_volume_m": 4200, "attention_level": 0.62, "relative_strength": 0.63},
    "XOM": {"market_cap_b": 500, "avg_dollar_volume_m": 3800, "attention_level": 0.76, "relative_strength": 0.78},
    "CVX": {"market_cap_b": 310, "avg_dollar_volume_m": 2600, "attention_level": 0.68, "relative_strength": 0.69},
    "DAL": {"market_cap_b": 35, "avg_dollar_volume_m": 900, "attention_level": 0.48, "relative_strength": 0.58},
    "LMT": {"market_cap_b": 130, "avg_dollar_volume_m": 800, "attention_level": 0.55, "relative_strength": 0.61},
    "NOC": {"market_cap_b": 70, "avg_dollar_volume_m": 520, "attention_level": 0.44, "relative_strength": 0.57},
    "WMT": {"market_cap_b": 520, "avg_dollar_volume_m": 3600, "attention_level": 0.60, "relative_strength": 0.51},
    "FSLR": {"market_cap_b": 28, "avg_dollar_volume_m": 1300, "attention_level": 0.52, "relative_strength": 0.62},
    "TSN": {"market_cap_b": 23, "avg_dollar_volume_m": 300, "attention_level": 0.24, "relative_strength": 0.47},
    "LEVI": {"market_cap_b": 8, "avg_dollar_volume_m": 120, "attention_level": 0.18, "relative_strength": 0.42},
    "STZ": {"market_cap_b": 48, "avg_dollar_volume_m": 600, "attention_level": 0.28, "relative_strength": 0.49},
    "LULU": {"market_cap_b": 37, "avg_dollar_volume_m": 1000, "attention_level": 0.46, "relative_strength": 0.52},
    "FIG": {"market_cap_b": 20, "avg_dollar_volume_m": 180, "attention_level": 0.34, "relative_strength": 0.55},
}


def infer_snapshot_from_news(news_rows: list[dict]) -> dict:
    snapshot = OrderedDict(
        as_of="",
        fear_greed=50.0,
        wti=80.0,
        vix=18.0,
        spx_qtd=0.0,
        us10y=4.0,
    )
    for row in news_rows:
        headline = normalize_text(row.get("headline")).lower()
        published = normalize_text(row.get("published_at"))
        if published and not snapshot["as_of"]:
            snapshot["as_of"] = published
        if "ceasefire" in headline or "停火" in headline:
            snapshot["fear_greed"] = 62.0
            snapshot["wti"] = 100.0
            snapshot["vix"] = 18.0
            snapshot["spx_qtd"] = 1.0
        if "war" in headline or "油价" in headline or "hormuz" in headline:
            snapshot["fear_greed"] = min(snapshot["fear_greed"], 35.0)
            snapshot["wti"] = max(snapshot["wti"], 105.0)
            snapshot["vix"] = max(snapshot["vix"], 24.0)
    return snapshot


def derive_candidate_record(raw: dict) -> dict:
    ticker = normalize_ticker(raw.get("ticker"))
    priors = MARKET_PRIORS.get(ticker, {})
    catalyst = normalize_text(raw.get("catalyst"))
    river = normalize_text(raw.get("river"))
    direction = normalize_text(raw.get("direction")).lower() or "long"
    attention = to_float(raw.get("attention_level"), None)
    if attention is None:
      attention = to_float(priors.get("attention_level"), 0.30) or 0.30
      if "earnings" in catalyst.lower():
          attention += 0.08
      if direction == "short":
          attention += 0.04
      attention = clamp(attention)
    rel = to_float(raw.get("relative_strength"), None)
    if rel is None:
      rel = clamp((to_float(priors.get("relative_strength"), 0.45) or 0.45) + (0.08 if direction == "long" else -0.02))
    hidden_catalyst_score = clamp(
        (0.72 if "earnings" in catalyst.lower() else 0.55)
        + (0.05 if "upgrade" in catalyst.lower() else 0.0)
        + (0.06 if "ceasefire" in catalyst.lower() or "停火" in catalyst.lower() else 0.0)
        - (0.08 if "ipo" in catalyst.lower() else 0.0)
    )
    evidence_edge = clamp(hidden_catalyst_score * 0.7 + (1.0 - attention) * 0.3)
    attention_gap = clamp(evidence_edge - attention + 0.15)
    return OrderedDict(
        ticker=ticker,
        name=normalize_text(raw.get("name")),
        sector=normalize_text(raw.get("sector")),
        catalyst=catalyst,
        strategic_river=river,
        direction=direction,
        market_cap_b=to_float(raw.get("market_cap_b"), to_float(priors.get("market_cap_b"), 15.0) or 15.0),
        avg_dollar_volume_m=to_float(raw.get("avg_dollar_volume_m"), to_float(priors.get("avg_dollar_volume_m"), 120.0) or 120.0),
        attention_level=round(attention, 4),
        relative_strength=round(rel, 4),
        attention_gap=round(attention_gap, 4),
        hidden_catalyst_score=round(hidden_catalyst_score, 4),
        evidence_edge=round(evidence_edge, 4),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Observe layer: infer short-horizon market snapshot and enrich candidate records")
    parser.add_argument("--task-slug", required=True)
    parser.add_argument("--raw-candidates")
    parser.add_argument("--news-log")
    parser.add_argument("--snapshot-output")
    parser.add_argument("--candidates-output")
    args = parser.parse_args()

    task_dir = ensure_task_dir(args.task_slug)
    raw_candidates_path = Path(args.raw_candidates) if args.raw_candidates else task_dir / "results" / "candidates" / "candidates.json"
    news_log_path = Path(args.news_log) if args.news_log else task_dir / "sources" / "news-event-log.jsonl"
    raw_candidates = read_json(raw_candidates_path, []) if raw_candidates_path.exists() else []
    news_rows = read_jsonl(news_log_path) if news_log_path.exists() else []

    snapshot = infer_snapshot_from_news(news_rows)
    enriched = [derive_candidate_record(item) for item in raw_candidates if normalize_ticker(item.get("ticker"))]

    snapshot_output = resolve_output(args.snapshot_output, task_dir, "sources/live-market-snapshot.json")
    candidates_output = resolve_output(args.candidates_output, task_dir, "results/candidates/candidates-enriched.json")
    write_json(snapshot_output, snapshot)
    write_json(candidates_output, enriched)
    print("SHORT_ALPHA_MARKET_OBSERVE_OK")
    print(f"SNAPSHOT={snapshot_output}")
    print(f"CANDIDATES={candidates_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
