#!/usr/bin/env python3

from __future__ import annotations

import argparse
from collections import OrderedDict
from pathlib import Path

from _short_alpha_common import read_json, resolve_output, ensure_task_dir, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply reviewer veto logic to short-alpha-general outputs")
    parser.add_argument("--task-slug")
    parser.add_argument("--regime-input", required=True)
    parser.add_argument("--campaign-input", required=True)
    parser.add_argument("--execution-input", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    task_dir = ensure_task_dir(args.task_slug) if args.task_slug else None
    regime = read_json(Path(args.regime_input), {})
    campaign = read_json(Path(args.campaign_input), {})
    execution = read_json(Path(args.execution_input), {})

    rows = execution.get("rows", [])
    failures = []
    if not rows:
        failures.append({
            "type": "empty_deployment",
            "message": "No deployment candidates were generated.",
            "owner": "execution-governor",
            "required_fix": "Generate campaign and execution outputs before review.",
        })

    strike_ready = [row for row in rows if row.get("status") == "strike-ready"]
    probe = [row for row in rows if row.get("status") == "probe"]
    watchlist = [row for row in rows if row.get("status") == "watchlist"]
    forbidden = [row for row in rows if row.get("status") == "forbidden"]

    for row in strike_ready:
        if row.get("truth_status") != "VERIFIED":
            failures.append({
                "type": "truth_mismatch",
                "message": f"{row.get('ticker')} is strike-ready without VERIFIED truth.",
                "owner": "execution-governor",
                "required_fix": "Downgrade or verify spot truth before strike-ready deployment.",
            })
        if row.get("deployment_tier") == "D":
            failures.append({
                "type": "desert_strike",
                "message": f"{row.get('ticker')} is strike-ready but sits in deployment tier D.",
                "owner": "campaign-score",
                "required_fix": "Do not deploy desert-tier opportunities as strike-ready.",
            })

    allowed_rivers = set(regime.get("allowed_strategic_rivers", []))
    forbidden_rivers = set(regime.get("forbidden_strategic_rivers", []))
    for row in campaign.get("rows", []):
        ticker = row.get("ticker")
        dao_alignment = float(row.get("dao_alignment", 0.0) or 0.0)
        if ticker and dao_alignment < 0.25:
            failures.append({
                "type": "dao_rejection",
                "message": f"{ticker} violates dao alignment.",
                "owner": "regime-engine",
                "required_fix": "Exclude forbidden strategic rivers from deployment candidates.",
            })

    if failures and not rows:
        status = "REVIEW_BLOCKED"
        can_generate_report = False
        allowed_output = "NONE"
    elif failures:
        status = "REVIEW_PASS_WITH_DEGRADATION"
        can_generate_report = True
        allowed_output = "WATCHLIST_ONLY"
    elif strike_ready:
        status = "REVIEW_PASS"
        can_generate_report = True
        allowed_output = "STRIKE_AND_PROBE"
    elif probe or watchlist:
        status = "REVIEW_PASS_WITH_DEGRADATION"
        can_generate_report = True
        allowed_output = "PROBE_OR_WATCHLIST_ONLY"
    else:
        status = "REVIEW_BLOCKED"
        can_generate_report = False
        allowed_output = "NONE"

    payload = OrderedDict(
        tool="short-alpha-general/review-gate",
        status=status,
        can_generate_report=can_generate_report,
        allowed_output=allowed_output,
        summary=OrderedDict(
            strike_ready=[row.get("ticker") for row in strike_ready],
            probe=[row.get("ticker") for row in probe],
            watchlist=[row.get("ticker") for row in watchlist],
            forbidden=[row.get("ticker") for row in forbidden],
            allowed_rivers=sorted(allowed_rivers),
            forbidden_rivers=sorted(forbidden_rivers),
        ),
        failures=failures,
        notes="short-alpha-general reviewer gate verdict",
    )
    output_path = resolve_output(args.output, task_dir, "reports/review/reviewer-verdict.json")
    write_json(output_path, payload)
    print("SHORT_ALPHA_REVIEW_GATE_OK")
    print(f"OUTPUT={output_path}")
    print(f"STATUS={status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
