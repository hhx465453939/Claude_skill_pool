#!/usr/bin/env python3

from __future__ import annotations

import argparse
from collections import OrderedDict
from pathlib import Path

from _short_alpha_common import normalize_ticker, read_json, read_rows, resolve_output, ensure_task_dir, to_float, write_json


def truth_status_for_ticker(ticker: str, truth_symbols: list[dict]) -> str:
    for item in truth_symbols:
        if normalize_ticker(item.get("symbol")) == ticker:
            return str(item.get("truth_status", "MISSING")).strip().upper() or "MISSING"
    return "MISSING"


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert campaign scores into strike/probe/watchlist/forbidden actions")
    parser.add_argument("--task-slug")
    parser.add_argument("--campaign-input", required=True)
    parser.add_argument("--truth-ledger-input")
    parser.add_argument("--output")
    args = parser.parse_args()

    task_dir = ensure_task_dir(args.task_slug) if args.task_slug else None
    campaign = read_json(Path(args.campaign_input), {})
    truth_path = Path(args.truth_ledger_input) if args.truth_ledger_input else (task_dir / "reports" / "derivatives" / "underlying-truth-ledger.json" if task_dir else None)
    truth_symbols = read_json(truth_path, {}).get("symbols", []) if truth_path and truth_path.exists() else []
    rows = []
    for row in campaign.get("rows", []):
        ticker = normalize_ticker(row.get("ticker"))
        if not ticker:
            continue
        campaign_score = to_float(row.get("campaign_score"), 0.0) or 0.0
        dao_alignment = to_float(row.get("dao_alignment"), 0.0) or 0.0
        timing_quality = to_float(row.get("timing_quality"), 0.0) or 0.0
        fertility_score = to_float(row.get("fertility_score"), 0.0) or 0.0
        tier = str(row.get("deployment_tier", "D"))
        truth_status = truth_status_for_ticker(ticker, truth_symbols)
        if truth_status == "VERIFIED" and campaign_score >= 0.72 and dao_alignment >= 0.60 and timing_quality >= 0.60 and tier in {"B", "C"}:
            status = "strike-ready"
        elif truth_status in {"VERIFIED", "PARTIAL"} and campaign_score >= 0.55 and fertility_score >= 0.50:
            status = "probe"
        elif campaign_score >= 0.40 and fertility_score >= 0.40:
            status = "watchlist"
        else:
            status = "forbidden"
        rows.append(
            OrderedDict(
                ticker=ticker,
                status=status,
                deployment_tier=tier,
                campaign_score=round(campaign_score, 4),
                dao_alignment=round(dao_alignment, 4),
                timing_quality=round(timing_quality, 4),
                fertility_score=round(fertility_score, 4),
                truth_status=truth_status,
                rationale=(
                    "truth+timing+fertility aligned"
                    if status == "strike-ready"
                    else "interesting but incomplete" if status == "probe"
                    else "observe and wait" if status == "watchlist"
                    else "do not deploy"
                ),
            )
        )

    rows.sort(key=lambda item: (item["status"], -item["campaign_score"]))
    payload = OrderedDict(
        tool="short-alpha-general/execution-governor",
        rows=rows,
        strike_ready=[item["ticker"] for item in rows if item["status"] == "strike-ready"],
        probe=[item["ticker"] for item in rows if item["status"] == "probe"],
        watchlist=[item["ticker"] for item in rows if item["status"] == "watchlist"],
        forbidden=[item["ticker"] for item in rows if item["status"] == "forbidden"],
    )
    output_path = resolve_output(args.output, task_dir, "results/execution/setup-quality.json")
    write_json(output_path, payload)
    print("SHORT_ALPHA_EXECUTION_GOVERNOR_OK")
    print(f"OUTPUT={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
