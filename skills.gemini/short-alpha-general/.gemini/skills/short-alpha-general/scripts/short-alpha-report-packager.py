#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from collections import OrderedDict
from pathlib import Path

from _short_alpha_common import ensure_task_dir, read_json, resolve_output


def format_ticker_block(title: str, tickers: list[str]) -> list[str]:
    lines = [f"## {title}", ""]
    if not tickers:
        lines.append("- none")
        lines.append("")
        return lines
    for ticker in tickers:
        lines.append(f"- {ticker}")
    lines.append("")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Package short-alpha-general outputs into a command brief")
    parser.add_argument("--task-slug", required=True)
    parser.add_argument("--regime-input")
    parser.add_argument("--pool-input")
    parser.add_argument("--review-input")
    parser.add_argument("--ooda-input")
    parser.add_argument("--registration-input")
    parser.add_argument("--calibration-input")
    parser.add_argument("--output")
    args = parser.parse_args()

    task_dir = ensure_task_dir(args.task_slug)
    regime = read_json(Path(args.regime_input) if args.regime_input else task_dir / "results" / "regime" / "regime-snapshot.json", {})
    pool = read_json(Path(args.pool_input) if args.pool_input else task_dir / "results" / "execution" / "deployment-pool.json", {})
    review = read_json(Path(args.review_input) if args.review_input else task_dir / "reports" / "review" / "reviewer-verdict.json", {})
    ooda = read_json(Path(args.ooda_input) if args.ooda_input else task_dir / "results" / "ooda" / "ooda-loop.json", {})
    registration = read_json(Path(args.registration_input) if args.registration_input else task_dir / "reports" / "short-alpha-general" / "strategy-registration.json", {})
    calibration = read_json(Path(args.calibration_input) if args.calibration_input else task_dir / "reports" / "short-alpha-general" / "score-calibration.json", {})

    output_path = resolve_output(args.output, task_dir, "reports/short-alpha-general/command-brief.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    summary = review.get("summary", {})
    lines = [
        "# Short Alpha General Command Brief",
        "",
        "## 执行摘要",
        "",
        f"- reviewer status: `{review.get('status', 'UNKNOWN')}`",
        f"- allowed output: `{review.get('allowed_output', 'UNKNOWN')}`",
        f"- regime: `{regime.get('regime', 'unknown')}`",
        f"- dao alignment: `{regime.get('dao_alignment', '')}`",
        "",
        "## 道天地将法判断",
        "",
        f"- 道: allowed rivers = {', '.join(regime.get('allowed_strategic_rivers', [])) or 'none'}",
        f"- 天: horizon = {regime.get('horizon', '')}",
        f"- 地: deployment tiers available = {', '.join([tier for tier, rows in pool.get('tiers', {}).items() if rows]) or 'none'}",
        f"- 将: reviewer gate = {review.get('status', 'UNKNOWN')}",
        f"- 法: failures = {len(review.get('failures', []))}",
        "",
        "## OODA",
        "",
        f"- Observe: regime={ooda.get('observe', {}).get('regime', '')}, events={ooda.get('observe', {}).get('event_count', '')}, truth_ready={ooda.get('observe', {}).get('truth_ready_count', '')}",
        f"- Orient: battlefield={ooda.get('orient', {}).get('primary_battlefield', '')}, fertile={', '.join(ooda.get('orient', {}).get('fertile_candidates', [])) or 'none'}, deserts={', '.join(ooda.get('orient', {}).get('deserts', [])) or 'none'}",
        f"- Decide: strike={', '.join(ooda.get('decide', {}).get('strike_ready', [])) or 'none'}, probe={', '.join(ooda.get('decide', {}).get('probe', [])) or 'none'}, watch={', '.join(ooda.get('decide', {}).get('watchlist', [])) or 'none'}",
        f"- Act: tempo={ooda.get('act', {}).get('tempo', '')}, intent={ooda.get('act', {}).get('command_intent', '')}",
        "",
        "## Strategy Pool",
        "",
        f"- registered strategies: {registration.get('registered_count', 0)}",
        f"- strike_ready_min: {calibration.get('threshold_hints', {}).get('strike_ready_min', '')}",
        f"- probe_min: {calibration.get('threshold_hints', {}).get('probe_min', '')}",
        f"- watchlist_min: {calibration.get('threshold_hints', {}).get('watchlist_min', '')}",
        "",
        "## 战场分层",
        "",
    ]

    for tier in ["A", "B", "C", "D"]:
        tier_rows = pool.get("tiers", {}).get(tier, [])
        tickers = [str(item.get("ticker", "")).strip() for item in tier_rows if str(item.get("ticker", "")).strip()]
        lines.append(f"- Tier {tier}: {', '.join(tickers) if tickers else 'none'}")
    lines.append("")
    lines.extend(format_ticker_block("Strike-Ready", summary.get("strike_ready", [])))
    lines.extend(format_ticker_block("Probe", summary.get("probe", [])))
    lines.extend(format_ticker_block("Watchlist", summary.get("watchlist", [])))
    lines.extend(format_ticker_block("Forbidden", summary.get("forbidden", [])))

    bot_handoff = OrderedDict(
        status=review.get("status", "UNKNOWN"),
        task_path=f"./tasks/{task_dir.name}",
        allowed_output=review.get("allowed_output", "UNKNOWN"),
        strike_ready=summary.get("strike_ready", []),
        probe=summary.get("probe", []),
        watchlist=summary.get("watchlist", []),
        forbidden=summary.get("forbidden", []),
    )
    lines.extend(
        [
            "## Bot Handoff",
            "",
            "```json",
            json.dumps(bot_handoff, ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print("SHORT_ALPHA_REPORT_PACKAGER_OK")
    print(f"OUTPUT={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
