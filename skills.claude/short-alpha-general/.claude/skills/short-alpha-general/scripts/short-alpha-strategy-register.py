#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from collections import OrderedDict
from pathlib import Path

from _short_alpha_common import ensure_task_dir, normalize_ticker, read_json, write_json, workspace_root


def ensure_strategy_dirs(task_dir: Path) -> Path:
    root = task_dir / "strategies" / "candidates"
    root.mkdir(parents=True, exist_ok=True)
    return root


def update_global_registry(entry: dict) -> None:
    workspace = workspace_root()
    registry_path = workspace / "strategy-pool" / "registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    payload = read_json(registry_path, {"tool": "market-alpha-strategy-pool", "strategies": [], "strategy_count": 0})
    strategies = [item for item in payload.get("strategies", []) if isinstance(item, dict)]
    replaced = False
    for idx, item in enumerate(strategies):
        if str(item.get("strategy_id", "")).strip() == entry["strategy_id"]:
            strategies[idx] = entry
            replaced = True
            break
    if not replaced:
        strategies.append(entry)
    payload["strategies"] = sorted(strategies, key=lambda item: str(item.get("strategy_id", "")))
    payload["strategy_count"] = len(payload["strategies"])
    payload["updated_at_utc"] = entry["updated_at_utc"]
    write_json(registry_path, payload)


def main() -> int:
    parser = argparse.ArgumentParser(description="Register short-alpha-general outputs into the shared strategy pool")
    parser.add_argument("--task-slug", required=True)
    parser.add_argument("--campaign-input", required=True)
    parser.add_argument("--execution-input", required=True)
    parser.add_argument("--review-input", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    task_dir = ensure_task_dir(args.task_slug)
    campaign = read_json(Path(args.campaign_input), {})
    execution = read_json(Path(args.execution_input), {})
    review = read_json(Path(args.review_input), {})
    campaign_rows = {normalize_ticker(item.get("ticker")): item for item in campaign.get("rows", []) if normalize_ticker(item.get("ticker"))}
    strategy_root = ensure_strategy_dirs(task_dir)
    registered = []

    for row in execution.get("rows", []):
        ticker = normalize_ticker(row.get("ticker"))
        if not ticker or row.get("status") not in {"strike-ready", "probe", "watchlist"}:
            continue
        campaign_row = campaign_rows.get(ticker, {})
        strategy_id = f"short-alpha-general-{ticker.lower()}-{row.get('deployment_tier', 'd').lower()}-{row.get('status', 'watchlist')}"
        candidate_dir = strategy_root / strategy_id
        candidate_dir.mkdir(parents=True, exist_ok=True)
        manifest = OrderedDict(
            strategy_id=strategy_id,
            name=f"Short Alpha General {ticker} {row.get('status')}",
            market="us",
            instrument="equity",
            style="short-horizon",
            horizon="w1-4",
            thesis_type="battle-plan",
            universe_rule="short-alpha-general filtered universe",
            signal_rule=f"campaign_score={row.get('campaign_score')} tier={row.get('deployment_tier')} status={row.get('status')}",
            factor_list=["dao_alignment", "timing_quality", "terrain_quality", "fertility_score", "campaign_score"],
            regime_tags=campaign.get("rows", [{}])[0].get("allowed_river", []) if False else [],
            validation_status="incubating" if row.get("status") == "strike-ready" else "draft",
            deployment_tier=row.get("deployment_tier"),
            campaign_score=row.get("campaign_score"),
            truth_status=row.get("truth_status"),
            reviewer_status=review.get("status", "UNKNOWN"),
            created_at_utc=review.get("updated_at_utc", ""),
            updated_at_utc=review.get("updated_at_utc", ""),
        )
        write_json(candidate_dir / "manifest.json", manifest)
        write_json(candidate_dir / "strategy-spec.json", OrderedDict(ticker=ticker, campaign=campaign_row, execution=row))
        write_json(candidate_dir / "factor-spec.json", OrderedDict(factors=manifest["factor_list"]))
        (candidate_dir / "thesis.md").write_text(
            f"# {ticker}\n\n- deployment_tier: {row.get('deployment_tier')}\n- status: {row.get('status')}\n- rationale: {row.get('rationale')}\n",
            encoding="utf-8",
        )
        global_entry = OrderedDict(manifest)
        global_entry["global_path"] = f"./{candidate_dir.relative_to(workspace_root()).as_posix()}" if workspace_root() in candidate_dir.parents else str(candidate_dir)
        update_global_registry(global_entry)
        registered.append(global_entry)

    payload = OrderedDict(
        tool="short-alpha-general/strategy-register",
        task_dir=str(task_dir),
        reviewer_status=review.get("status", "UNKNOWN"),
        registered_count=len(registered),
        strategies=registered,
    )
    output_path = Path(args.output) if args.output else task_dir / "reports" / "short-alpha-general" / "strategy-registration.json"
    write_json(output_path, payload)
    print("SHORT_ALPHA_STRATEGY_REGISTER_OK")
    print(f"OUTPUT={output_path}")
    print(f"REGISTERED={len(registered)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
