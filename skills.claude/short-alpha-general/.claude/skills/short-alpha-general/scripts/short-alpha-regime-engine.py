#!/usr/bin/env python3

from __future__ import annotations

import argparse
from collections import OrderedDict
from pathlib import Path

from _short_alpha_common import clamp, read_json, resolve_output, ensure_task_dir, to_float, write_json


def infer_regime(snapshot: dict, horizon: str) -> dict:
    fear_greed = to_float(snapshot.get("fear_greed"), 50.0) or 50.0
    oil = to_float(snapshot.get("wti"), 80.0) or 80.0
    vix = to_float(snapshot.get("vix"), 18.0) or 18.0
    spx_qtd = to_float(snapshot.get("spx_qtd"), 0.0) or 0.0
    ten_year = to_float(snapshot.get("us10y"), 4.0) or 4.0

    if fear_greed < 25 or vix > 25 or oil > 100:
        regime = "event-driven-risk-off"
    elif spx_qtd > 3 and vix < 18:
        regime = "trend-risk-on"
    else:
        regime = "mixed-transition"

    macro_weight_map = {
        "h4-1d": 0.10,
        "d1-5": 0.10,
        "w1-2": 0.15,
        "w1-4": 0.18,
        "m1-3": 0.22,
    }
    macro_weight = macro_weight_map.get(horizon, 0.18)

    allowed = ["relative-strength", "attention-gap", "idiosyncratic-post-event", "forced-flow-follow-through"]
    forbidden = []
    if regime == "event-driven-risk-off":
        allowed.extend(["defense-adjacent", "earnings-repricing", "boring-cashflow-compounders"])
        forbidden.extend(["crowded-war-commodity-chase", "high-duration-meme-beta"])
    elif regime == "trend-risk-on":
        allowed.extend(["breakout-continuation", "post-earnings-drift"])
        forbidden.extend(["deep-value-no-catalyst"])
    else:
        allowed.extend(["mean-reversion-with-catalyst", "short-squeeze-reset"])
        forbidden.extend(["macro-thesis-only"])

    dao_alignment = clamp(0.45 + (0.12 if regime == "event-driven-risk-off" else 0.08) + (0.08 if ten_year > 4.1 else 0.0))
    return {
        "regime": regime,
        "macro_weight": macro_weight,
        "dao_alignment": round(dao_alignment, 4),
        "allowed_strategic_rivers": allowed,
        "forbidden_strategic_rivers": forbidden,
        "inputs": {
            "fear_greed": fear_greed,
            "wti": oil,
            "vix": vix,
            "spx_qtd": spx_qtd,
            "us10y": ten_year,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Infer short-horizon regime and dao alignment")
    parser.add_argument("--task-slug")
    parser.add_argument("--market", default="us")
    parser.add_argument("--horizon", default="w1-4")
    parser.add_argument("--input")
    parser.add_argument("--output")
    args = parser.parse_args()

    task_dir = ensure_task_dir(args.task_slug) if args.task_slug else None
    input_path = Path(args.input) if args.input else (task_dir / "sources" / "live-market-snapshot.json" if task_dir else None)
    snapshot = read_json(input_path, {}) if input_path and input_path.exists() else {}
    payload = OrderedDict(
        tool="short-alpha-general/regime-engine",
        market=args.market,
        horizon=args.horizon,
        as_of=str(snapshot.get("as_of", "")),
        **infer_regime(snapshot, args.horizon),
    )
    output_path = resolve_output(args.output, task_dir, "results/regime/regime-snapshot.json")
    write_json(output_path, payload)
    print("SHORT_ALPHA_REGIME_ENGINE_OK")
    print(f"OUTPUT={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
