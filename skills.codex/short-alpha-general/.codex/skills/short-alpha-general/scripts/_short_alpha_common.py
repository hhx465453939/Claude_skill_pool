#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
from pathlib import Path
import sys
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
def _detect_workspace_dir() -> Path:
    current = SCRIPT_DIR
    for candidate in [current, *current.parents]:
        if candidate.name == "workspace":
            return candidate
    return SCRIPT_DIR.parent.parent.parent


WORKSPACE_DIR = _detect_workspace_dir()
TASK_SCRIPT_DIR = WORKSPACE_DIR / "scripts"
if str(TASK_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(TASK_SCRIPT_DIR))

import task_session  # noqa: E402


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def read_json(path: Path, default: Any) -> Any:
    return task_session.read_json(path, default)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def read_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".json":
        payload = read_json(path, {})
        if isinstance(payload, list):
            return [dict(item) for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            for key in ["rows", "candidates", "records", "opportunities", "tickers", "items"]:
                value = payload.get(key)
                if isinstance(value, list):
                    return [dict(item) for item in value if isinstance(item, dict)]
        return []
    if path.suffix.lower() == ".jsonl":
        return read_jsonl(path)
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    raise SystemExit(f"Unsupported input type: {path}")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def to_float(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    if text in {"", "NA", "N/A", "null", "None", "."}:
        return default
    try:
        return float(text)
    except ValueError:
        return default


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def normalize_ticker(value: Any) -> str:
    return normalize_text(value).upper()


def ensure_task_dir(task_slug: str | None) -> Path:
    try:
        return task_session.resolve_task_dir(task_slug=task_slug, prefer_active=True)
    except SystemExit:
        if task_slug:
            candidates = sorted((WORKSPACE_DIR / "tasks").glob(f"*-{task_slug}"), reverse=True)
            if candidates:
                return candidates[0]
        raise


def workspace_root() -> Path:
    return WORKSPACE_DIR


def resolve_output(path_arg: str | None, task_dir: Path | None, default_rel: str) -> Path:
    if path_arg:
        path = Path(path_arg)
        return path if path.is_absolute() else (WORKSPACE_DIR / path).resolve()
    if task_dir is None:
        raise SystemExit("Either --task-slug or explicit output path is required")
    return task_dir / default_rel


def resolve_input(path_arg: str | None, task_dir: Path | None, default_rel: str | None = None) -> Path | None:
    if path_arg:
        path = Path(path_arg)
        return path if path.is_absolute() else (WORKSPACE_DIR / path).resolve()
    if task_dir is None or default_rel is None:
        return None
    candidate = task_dir / default_rel
    return candidate if candidate.exists() else None


def score_to_tier(capacity_score: float, crowding_score: float, fertility_score: float) -> str:
    if fertility_score < 0.35 or capacity_score < 0.15:
        return "D"
    if capacity_score >= 0.75 and crowding_score >= 0.65:
        return "A"
    if capacity_score >= 0.40 and fertility_score >= 0.55:
        return "B"
    if fertility_score >= 0.60:
        return "C"
    return "D"
