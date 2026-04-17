#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = SCRIPT_DIR.parent.parent.parent
TASK_SCRIPT_DIR = WORKSPACE_DIR / "scripts"
sys.path.insert(0, str(TASK_SCRIPT_DIR))

import task_session  # noqa: E402


DEFAULT_RELATIVE_PATHS = [
    "README.md",
    "meta.json",
    "notes.md",
    "qa.jsonl",
    "agents.jsonl",
    "scripts.jsonl",
    "artifacts.jsonl",
    "capsules",
    "agents",
    "reports",
    "scripts",
]


def iter_paths(task_dir: Path, include_sources: bool, include_scratch: bool):
    for rel in DEFAULT_RELATIVE_PATHS:
        path = task_dir / rel
        if path.exists():
            yield path
    if include_sources:
        path = task_dir / "sources"
        if path.exists():
            yield path
    if include_scratch:
        path = task_dir / "scratch"
        if path.exists():
            yield path


def add_path(zf: zipfile.ZipFile, base_dir: Path, path: Path) -> None:
    if path.is_file():
        zf.write(path, arcname=str(path.relative_to(base_dir)))
        return
    for file in sorted(path.rglob("*")):
        if file.is_file():
            zf.write(file, arcname=str(file.relative_to(base_dir)))


def main() -> int:
    parser = argparse.ArgumentParser(description="Package a market-alpha task for optional Feishu delivery")
    parser.add_argument("--task-slug")
    parser.add_argument("--include-sources", action="store_true")
    parser.add_argument("--include-scratch", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()

    task_dir = task_session.resolve_task_dir(task_slug=args.task_slug, prefer_active=True)
    task_slug = task_dir.name.split("-", 3)[-1] if "-" in task_dir.name else task_dir.name
    artifacts_dir = task_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    output_path = Path(args.output) if args.output else artifacts_dir / f"{task_slug}-market-alpha-bundle.zip"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in iter_paths(task_dir, include_sources=args.include_sources, include_scratch=args.include_scratch):
            add_path(zf, task_dir, path)

    payload = {
        "timestamp_utc": task_session.iso_now(),
        "path": str(output_path),
        "kind": "task-package",
        "note": json.dumps(
            {
                "include_sources": args.include_sources,
                "include_scratch": args.include_scratch,
            },
            ensure_ascii=False,
        ),
    }
    task_session.append_jsonl(task_dir / "artifacts.jsonl", payload)

    relative = f".{str(output_path).replace(str(WORKSPACE_DIR), '')}"
    print("MARKET_ALPHA_TASK_PACKAGE_OK")
    print(f"TASK_DIR={task_dir}")
    print(f"PACKAGE={output_path}")
    print(f"RELATIVE_PATH={relative}")
    print(f'FEISHU_SEND_FILE_PAYLOAD={{"action":"upload_and_send","file_path":"{relative[2:]}"}}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
