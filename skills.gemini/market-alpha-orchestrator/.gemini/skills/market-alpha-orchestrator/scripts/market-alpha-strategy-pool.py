#!/usr/bin/env python3

from __future__ import annotations

import argparse
import shutil
from collections import OrderedDict
from pathlib import Path
import sys
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = SCRIPT_DIR.parent.parent.parent
TASK_SCRIPT_DIR = WORKSPACE_DIR / "scripts"
sys.path.insert(0, str(TASK_SCRIPT_DIR))

import task_session  # noqa: E402


VALIDATION_STATUSES = [
    "draft",
    "incubating",
    "validated",
    "paper",
    "live_candidate",
    "live",
    "degraded",
    "quarantined",
    "retired",
]


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def task_strategy_paths(task_dir: Path) -> dict[str, Path]:
    strategy_root = task_dir / "strategies"
    reports_root = task_dir / "reports" / "strategy-lab"
    return {
        "strategy_root": strategy_root,
        "candidates": strategy_root / "candidates",
        "experiments": strategy_root / "experiments",
        "reviews": strategy_root / "reviews",
        "promotion": strategy_root / "promotion",
        "reports_root": reports_root,
        "registry_preview": reports_root / "registry-preview.json",
        "factor_library": reports_root / "factor-library.json",
        "strategy_ranking": reports_root / "strategy-ranking.json",
    }


def global_strategy_paths() -> dict[str, Path]:
    root = WORKSPACE_DIR / "strategy-pool"
    return {
        "root": root,
        "strategies": root / "strategies",
        "registry": root / "registry.json",
    }


def load_json(path: Path, default: Any) -> Any:
    return task_session.read_json(path, default)


def refresh_task_registry(task_dir: Path) -> OrderedDict[str, Any]:
    paths = task_strategy_paths(task_dir)
    paths["candidates"].mkdir(parents=True, exist_ok=True)
    manifests: list[dict[str, Any]] = []
    factor_names: set[str] = set()

    for manifest_path in sorted(paths["candidates"].glob("*/manifest.json")):
        payload = load_json(manifest_path, {})
        if not isinstance(payload, dict) or not payload:
            continue
        payload["manifest_path"] = f"./{manifest_path.relative_to(WORKSPACE_DIR).as_posix()}"
        manifests.append(payload)
        for factor in payload.get("factor_list", []):
            factor_text = str(factor).strip()
            if factor_text:
                factor_names.add(factor_text)

    ranked = sorted(
        manifests,
        key=lambda item: (
            VALIDATION_STATUSES.index(str(item.get("validation_status", "draft")))
            if str(item.get("validation_status", "draft")) in VALIDATION_STATUSES
            else 999,
            str(item.get("strategy_id", "")),
        ),
    )

    registry_preview = OrderedDict(
        tool="market-alpha-strategy-pool",
        updated_at_utc=task_session.iso_now(),
        task_dir=str(task_dir),
        strategy_count=len(manifests),
        strategies=manifests,
    )
    factor_library = OrderedDict(
        tool="market-alpha-strategy-pool",
        updated_at_utc=task_session.iso_now(),
        factor_count=len(factor_names),
        factors=sorted(factor_names),
    )
    strategy_ranking = OrderedDict(
        tool="market-alpha-strategy-pool",
        updated_at_utc=task_session.iso_now(),
        ranked_strategy_ids=[str(item.get("strategy_id", "")).strip() for item in ranked if str(item.get("strategy_id", "")).strip()],
    )

    task_session.write_json(paths["registry_preview"], registry_preview)
    task_session.write_json(paths["factor_library"], factor_library)
    task_session.write_json(paths["strategy_ranking"], strategy_ranking)
    return registry_preview


def cmd_init_task_lab(args: argparse.Namespace) -> int:
    task_dir = task_session.resolve_task_dir(task_slug=args.task_slug, prefer_active=True)
    paths = task_strategy_paths(task_dir)
    for path in paths.values():
        if path.suffix:
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            path.mkdir(parents=True, exist_ok=True)

    write_text(
        paths["strategy_root"] / "README.md",
        f"""# Market Alpha Strategy Lab

- market: `{args.market}`
- style: `{args.style}`
- horizon: `{args.horizon}`
- objective: `{args.objective or 'N/A'}`

## Lifecycle

- `draft -> incubating -> validated -> paper -> live_candidate -> live -> degraded -> quarantined -> retired`

## Layout

- `candidates/`
- `experiments/`
- `reviews/`
- `promotion/`
- `reports/strategy-lab/*.json`
""",
    )

    refresh_task_registry(task_dir)
    global_paths = global_strategy_paths()
    global_paths["strategies"].mkdir(parents=True, exist_ok=True)
    if not global_paths["registry"].exists():
        task_session.write_json(
            global_paths["registry"],
            OrderedDict(
                tool="market-alpha-strategy-pool",
                updated_at_utc=task_session.iso_now(),
                strategy_count=0,
                strategies=[],
            ),
        )

    print("MARKET_ALPHA_STRATEGY_POOL_INIT_OK")
    print(f"TASK_DIR={task_dir}")
    print(f"STRATEGY_ROOT={paths['strategy_root']}")
    return 0


def normalize_csv_list(raw: str) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for item in str(raw or "").split(","):
        cleaned = item.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            values.append(cleaned)
    return values


def cmd_register_candidate(args: argparse.Namespace) -> int:
    task_dir = task_session.resolve_task_dir(task_slug=args.task_slug, prefer_active=True)
    paths = task_strategy_paths(task_dir)
    strategy_id = task_session.slugify(args.strategy_id)
    validation_status = str(args.validation_status or "draft").strip().lower()
    if validation_status not in VALIDATION_STATUSES:
        raise SystemExit(f"invalid validation status: {validation_status}")

    candidate_dir = paths["candidates"] / strategy_id
    candidate_dir.mkdir(parents=True, exist_ok=True)
    manifest = OrderedDict(
        strategy_id=strategy_id,
        name=str(args.name).strip(),
        market=str(args.market).strip(),
        instrument=str(args.instrument).strip(),
        style=str(args.style).strip(),
        horizon=str(args.horizon).strip(),
        thesis_type=str(args.thesis_type).strip(),
        universe_rule=str(args.universe_rule).strip(),
        signal_rule=str(args.signal_rule).strip(),
        factor_list=normalize_csv_list(args.factor_list),
        regime_tags=normalize_csv_list(args.regime_tags),
        validation_status=validation_status,
        created_at_utc=task_session.iso_now(),
        updated_at_utc=task_session.iso_now(),
    )
    task_session.write_json(candidate_dir / "manifest.json", manifest)
    task_session.write_json(candidate_dir / "strategy-spec.json", OrderedDict(strategy_id=strategy_id, thesis=str(args.thesis or "").strip()))
    task_session.write_json(candidate_dir / "factor-spec.json", OrderedDict(strategy_id=strategy_id, factors=normalize_csv_list(args.factor_list)))
    write_text(candidate_dir / "thesis.md", str(args.thesis or "").strip() or f"# {args.name}\n")
    refresh_task_registry(task_dir)

    print("MARKET_ALPHA_STRATEGY_POOL_REGISTER_OK")
    print(f"STRATEGY_ID={strategy_id}")
    print(f"CANDIDATE_DIR={candidate_dir}")
    return 0


def cmd_refresh_task_lab(args: argparse.Namespace) -> int:
    task_dir = task_session.resolve_task_dir(task_slug=args.task_slug, prefer_active=True)
    registry = refresh_task_registry(task_dir)
    print("MARKET_ALPHA_STRATEGY_POOL_REFRESH_OK")
    print(f"TASK_DIR={task_dir}")
    print(f"STRATEGY_COUNT={registry.get('strategy_count', 0)}")
    return 0


def cmd_promote(args: argparse.Namespace) -> int:
    task_dir = task_session.resolve_task_dir(task_slug=args.task_slug, prefer_active=True)
    paths = task_strategy_paths(task_dir)
    global_paths = global_strategy_paths()
    strategy_id = task_session.slugify(args.strategy_id)
    candidate_dir = paths["candidates"] / strategy_id
    manifest_path = candidate_dir / "manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"candidate manifest not found: {manifest_path}")

    manifest = load_json(manifest_path, {})
    if not isinstance(manifest, dict) or not manifest:
        raise SystemExit(f"invalid candidate manifest: {manifest_path}")

    promoted_dir = global_paths["strategies"] / strategy_id
    if promoted_dir.exists():
        shutil.rmtree(promoted_dir)
    promoted_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(candidate_dir, promoted_dir)

    registry = load_json(global_paths["registry"], {})
    strategies = [item for item in registry.get("strategies", []) if isinstance(item, dict)]
    manifest["validation_status"] = str(args.validation_status or manifest.get("validation_status") or "validated").strip().lower()
    manifest["promoted_from"] = f"./{candidate_dir.relative_to(WORKSPACE_DIR).as_posix()}"
    manifest["updated_at_utc"] = task_session.iso_now()
    manifest["global_path"] = f"./{promoted_dir.relative_to(WORKSPACE_DIR).as_posix()}"

    replaced = False
    for index, item in enumerate(strategies):
        if str(item.get("strategy_id", "")).strip() == strategy_id:
            strategies[index] = manifest
            replaced = True
            break
    if not replaced:
        strategies.append(manifest)

    payload = OrderedDict(
        tool="market-alpha-strategy-pool",
        updated_at_utc=task_session.iso_now(),
        strategy_count=len(strategies),
        strategies=sorted(strategies, key=lambda item: str(item.get("strategy_id", ""))),
    )
    task_session.write_json(global_paths["registry"], payload)
    task_session.write_json(
        paths["promotion"] / f"{strategy_id}.json",
        OrderedDict(
            strategy_id=strategy_id,
            promoted_at_utc=task_session.iso_now(),
            validation_status=manifest["validation_status"],
            global_path=manifest["global_path"],
        ),
    )

    print("MARKET_ALPHA_STRATEGY_POOL_PROMOTE_OK")
    print(f"STRATEGY_ID={strategy_id}")
    print(f"GLOBAL_PATH={promoted_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage task-local and global strategy-pool state for market-alpha")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init-task-lab")
    init.add_argument("--task-slug")
    init.add_argument("--market", default="multi")
    init.add_argument("--style", default="hybrid")
    init.add_argument("--horizon", default="auto")
    init.add_argument("--objective", default="")
    init.set_defaults(func=cmd_init_task_lab)

    register = subparsers.add_parser("register-candidate")
    register.add_argument("--task-slug")
    register.add_argument("--strategy-id", required=True)
    register.add_argument("--name", required=True)
    register.add_argument("--market", required=True)
    register.add_argument("--instrument", default="equity")
    register.add_argument("--style", required=True)
    register.add_argument("--horizon", required=True)
    register.add_argument("--thesis-type", default="pattern")
    register.add_argument("--universe-rule", default="")
    register.add_argument("--signal-rule", default="")
    register.add_argument("--factor-list", default="")
    register.add_argument("--regime-tags", default="")
    register.add_argument("--validation-status", default="draft")
    register.add_argument("--thesis", default="")
    register.set_defaults(func=cmd_register_candidate)

    refresh = subparsers.add_parser("refresh-task-lab")
    refresh.add_argument("--task-slug")
    refresh.set_defaults(func=cmd_refresh_task_lab)

    promote = subparsers.add_parser("promote")
    promote.add_argument("--task-slug")
    promote.add_argument("--strategy-id", required=True)
    promote.add_argument("--validation-status", default="validated")
    promote.set_defaults(func=cmd_promote)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
