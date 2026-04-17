#!/usr/bin/env python3

from __future__ import annotations

import argparse
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

from _short_alpha_common import normalize_text, normalize_ticker, read_rows, resolve_output, ensure_task_dir, write_json


def parse_iso(value: str | None) -> datetime | None:
    text = normalize_text(value)
    if not text:
        return None
    try:
        if text.endswith("Z"):
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def event_quality(event_type: str, days_to_event: int | None) -> float:
    base = {
        "earnings": 0.82,
        "guidance": 0.76,
        "policy": 0.70,
        "opec": 0.72,
        "launch": 0.66,
        "conference": 0.55,
    }.get(event_type.lower(), 0.50)
    if days_to_event is None:
        return max(0.30, base - 0.20)
    if days_to_event <= 3:
        return min(1.0, base + 0.12)
    if days_to_event <= 10:
        return min(1.0, base + 0.05)
    if days_to_event <= 20:
        return base
    return max(0.25, base - 0.15)


def window_label(days_to_event: int | None, quality: float) -> str:
    if days_to_event is None:
        return "watch"
    if quality >= 0.72 and days_to_event <= 10:
        return "strike"
    if quality >= 0.52 and days_to_event <= 20:
        return "probe"
    return "watch"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a short-horizon event clock from task-local event records")
    parser.add_argument("--task-slug")
    parser.add_argument("--events-input")
    parser.add_argument("--timeline-output")
    parser.add_argument("--watchlist-output")
    parser.add_argument("--as-of")
    args = parser.parse_args()

    task_dir = ensure_task_dir(args.task_slug) if args.task_slug else None
    input_path = Path(args.events_input) if args.events_input else (task_dir / "sources" / "news-event-log.jsonl" if task_dir else None)
    rows = read_rows(input_path) if input_path and input_path.exists() else []
    as_of_dt = parse_iso(args.as_of) or datetime.now(timezone.utc)
    events: list[dict] = []
    by_ticker: dict[str, list[dict]] = {}

    for row in rows:
        ticker = normalize_ticker(row.get("symbol") or row.get("ticker"))
        if not ticker:
            continue
        event_at = parse_iso(str(row.get("published_at") or row.get("event_at") or row.get("publishedAt") or ""))
        days = None
        if event_at is not None:
            days = max(0, int((event_at - as_of_dt).total_seconds() // 86400))
        event_type = normalize_text(row.get("event_type") or row.get("driver_type") or "generic")
        quality = round(event_quality(event_type, days), 4)
        record = OrderedDict(
            ticker=ticker,
            event_type=event_type,
            headline=normalize_text(row.get("headline")),
            event_at=event_at.isoformat().replace("+00:00", "Z") if event_at else "",
            days_to_event=days,
            attention_window=window_label(days, quality),
            event_quality=quality,
            impact_horizon=normalize_text(row.get("impact_horizon")),
        )
        events.append(record)
        by_ticker.setdefault(ticker, []).append(record)

    for ticker, items in by_ticker.items():
        items.sort(key=lambda item: (item["days_to_event"] is None, item["days_to_event"] or 9999, -item["event_quality"]))

    watchlist = []
    for ticker, items in sorted(by_ticker.items()):
        top = items[0]
        watchlist.append(
            OrderedDict(
                ticker=ticker,
                top_event_type=top["event_type"],
                top_event_at=top["event_at"],
                top_event_quality=top["event_quality"],
                action_window=top["attention_window"],
            )
        )

    timeline_payload = OrderedDict(
        tool="short-alpha-general/event-clock",
        as_of=as_of_dt.isoformat().replace("+00:00", "Z"),
        events=events,
    )
    watchlist_payload = OrderedDict(
        tool="short-alpha-general/event-clock",
        as_of=as_of_dt.isoformat().replace("+00:00", "Z"),
        watchlist=watchlist,
    )

    timeline_output = resolve_output(args.timeline_output, task_dir, "results/event-clock/catalyst-timeline.json")
    watchlist_output = resolve_output(args.watchlist_output, task_dir, "results/event-clock/trigger-watchlist.json")
    write_json(timeline_output, timeline_payload)
    write_json(watchlist_output, watchlist_payload)
    print("SHORT_ALPHA_EVENT_CLOCK_OK")
    print(f"TIMELINE={timeline_output}")
    print(f"WATCHLIST={watchlist_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
