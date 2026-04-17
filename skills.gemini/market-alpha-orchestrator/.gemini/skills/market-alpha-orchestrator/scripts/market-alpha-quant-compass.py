#!/usr/bin/env python3
"""
Market Alpha Quant Compass

为 market-alpha task 提供最小但真实可执行的量化能力：
- 因子标准化评分
- 简单线性回归
- lead-lag 相关性扫描
- 分桶评估
- 基于 forward return 的信号回测
- 运行时硬件检测与模型路由建议

要求：
- 只依赖 Python 标准库
- 输入优先为 task-local CSV / JSON
- 对 score / backtest / lead-lag / bucket-eval 在写 JSON 时自动生成 CSV 和 PNG companion
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import shutil
import statistics
import struct
import subprocess
import zlib
from collections import OrderedDict
from pathlib import Path
from typing import Any


def read_rows(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [dict(item) for item in data]
        if isinstance(data, dict) and isinstance(data.get("rows"), list):
            return [dict(item) for item in data["rows"]]
        raise SystemExit(f"Unsupported JSON structure in {path}")
    if suffix == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    raise SystemExit(f"Unsupported input type: {path}")


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if math.isnan(value) or math.isinf(value):
            return None
        return float(value)
    text = str(value).strip().replace(",", "")
    if text in {"", "NA", "N/A", "null", "None", "."}:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y", "buy", "long", "signal"}


def calc_stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = statistics.mean(values)
    return math.sqrt(sum((v - avg) ** 2 for v in values) / (len(values) - 1))


def zscore(value: float, values: list[float]) -> float:
    avg = statistics.mean(values)
    sd = calc_stdev(values)
    if sd == 0:
        return 0.0
    return (value - avg) / sd


def parse_factor_spec(spec: str) -> list[tuple[str, float]]:
    result: list[tuple[str, float]] = []
    for item in spec.split(","):
        raw = item.strip()
        if not raw:
            continue
        name, _, weight = raw.partition(":")
        if not name or not weight:
            raise SystemExit(f"Invalid factor spec: {raw}")
        result.append((name.strip(), float(weight)))
    if not result:
        raise SystemExit("No valid factor definitions")
    return result


def parse_factor_names(spec: str) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for item in str(spec or "").split(","):
        cleaned = item.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            names.append(cleaned)
    return names


def ensure_parent(path: str | None) -> None:
    if not path:
        return
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def json_output_path(path: str | None) -> Path | None:
    return Path(path) if path else None


def default_companion_path(path: str | None, suffix: str) -> Path | None:
    if not path:
        return None
    base = Path(path)
    return base.with_suffix(suffix)


def write_json(path: str | None, payload: Any) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if path:
        ensure_parent(path)
        Path(path).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def numeric_column_names(rows: list[dict[str, Any]], exclude: set[str] | None = None) -> list[str]:
    exclude = {item.lower() for item in (exclude or set())}
    names: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row.keys():
            normalized = str(key).strip()
            lowered = normalized.lower()
            if lowered in exclude or lowered in seen:
                continue
            if to_float(row.get(key)) is None:
                continue
            seen.add(lowered)
            names.append(normalized)
    return names


def write_csv(path: Path | None, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def pack_chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def save_png(path: Path, width: int, height: int, pixels: bytearray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = bytearray()
    row_bytes = width * 3
    for y in range(height):
        raw.append(0)
        start = y * row_bytes
        raw.extend(pixels[start : start + row_bytes])

    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png.extend(pack_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)))
    png.extend(pack_chunk(b"IDAT", zlib.compress(bytes(raw), level=9)))
    png.extend(pack_chunk(b"IEND", b""))
    path.write_bytes(bytes(png))


def make_canvas(width: int, height: int, color: tuple[int, int, int] = (255, 255, 255)) -> bytearray:
    pixels = bytearray(width * height * 3)
    r, g, b = color
    for idx in range(0, len(pixels), 3):
        pixels[idx] = r
        pixels[idx + 1] = g
        pixels[idx + 2] = b
    return pixels


def set_pixel(pixels: bytearray, width: int, height: int, x: int, y: int, color: tuple[int, int, int]) -> None:
    if x < 0 or y < 0 or x >= width or y >= height:
        return
    idx = (y * width + x) * 3
    pixels[idx] = color[0]
    pixels[idx + 1] = color[1]
    pixels[idx + 2] = color[2]


def draw_rect(
    pixels: bytearray,
    width: int,
    height: int,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    color: tuple[int, int, int],
) -> None:
    left, right = sorted((x0, x1))
    top, bottom = sorted((y0, y1))
    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            set_pixel(pixels, width, height, x, y, color)


def draw_line(
    pixels: bytearray,
    width: int,
    height: int,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    color: tuple[int, int, int],
) -> None:
    dx = abs(x1 - x0)
    sx = 1 if x0 < x1 else -1
    dy = -abs(y1 - y0)
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        set_pixel(pixels, width, height, x0, y0, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def render_bar_chart(
    output: Path,
    values: list[float],
    positive_color: tuple[int, int, int] = (38, 166, 154),
    negative_color: tuple[int, int, int] = (229, 57, 53),
) -> None:
    width = 960
    height = 540
    left = 60
    right = 30
    top = 30
    bottom = 60
    plot_width = width - left - right
    plot_height = height - top - bottom
    pixels = make_canvas(width, height)

    axis_color = (90, 90, 90)
    draw_line(pixels, width, height, left, top, left, top + plot_height, axis_color)
    draw_line(pixels, width, height, left, top + plot_height, left + plot_width, top + plot_height, axis_color)

    if not values:
        save_png(output, width, height, pixels)
        return

    max_value = max(values)
    min_value = min(values)
    if max_value == min_value:
        max_value = min_value + 1.0

    zero_y = top + plot_height
    if min_value < 0 < max_value:
        zero_y = top + int(plot_height * (max_value / (max_value - min_value)))
        draw_line(pixels, width, height, left, zero_y, left + plot_width, zero_y, (160, 160, 160))

    bar_count = len(values)
    slot_width = plot_width / max(bar_count, 1)
    bar_width = max(8, int(slot_width * 0.6))

    for idx, value in enumerate(values):
        x_center = left + int(slot_width * idx + slot_width / 2)
        x0 = x_center - bar_width // 2
        x1 = x_center + bar_width // 2
        if min_value < 0 < max_value:
            if value >= 0:
                y = zero_y - int((value / max_value) * (zero_y - top)) if max_value else zero_y
                draw_rect(pixels, width, height, x0, y, x1, zero_y, positive_color)
            else:
                y = zero_y + int((abs(value) / abs(min_value)) * ((top + plot_height) - zero_y)) if min_value else zero_y
                draw_rect(pixels, width, height, x0, zero_y, x1, y, negative_color)
        else:
            scaled = (value - min_value) / (max_value - min_value)
            y = top + plot_height - int(scaled * plot_height)
            draw_rect(pixels, width, height, x0, y, x1, top + plot_height, positive_color if value >= 0 else negative_color)

    save_png(output, width, height, pixels)


def maybe_write_companions(
    json_path: str | None,
    csv_rows: list[dict[str, Any]] | None = None,
    csv_fields: list[str] | None = None,
    png_values: list[float] | None = None,
) -> dict[str, str]:
    outputs: dict[str, str] = {}
    if not json_path:
        return outputs
    json_file = Path(json_path)
    if csv_rows is not None and csv_fields is not None:
        csv_path = default_companion_path(json_path, ".csv")
        if csv_path is not None:
            write_csv(csv_path, csv_fields, csv_rows)
            outputs["csv"] = str(csv_path)
    if png_values is not None:
        png_path = default_companion_path(json_path, ".png")
        if png_path is not None:
            render_bar_chart(png_path, png_values)
            outputs["png"] = str(png_path)
    return outputs


def simple_linear_regression(xs: list[float], ys: list[float]) -> dict[str, float]:
    if len(xs) != len(ys):
        raise SystemExit("x/y length mismatch")
    if len(xs) < 2:
        raise SystemExit("Need at least 2 observations for regression")
    x_bar = statistics.mean(xs)
    y_bar = statistics.mean(ys)
    sxx = sum((x - x_bar) ** 2 for x in xs)
    sxy = sum((x - x_bar) * (y - y_bar) for x, y in zip(xs, ys))
    syy = sum((y - y_bar) ** 2 for y in ys)
    if sxx == 0:
        raise SystemExit("x has zero variance")
    slope = sxy / sxx
    intercept = y_bar - slope * x_bar
    correlation = 0.0 if syy == 0 else sxy / math.sqrt(sxx * syy)
    residuals = [y - (intercept + slope * x) for x, y in zip(xs, ys)]
    rmse = math.sqrt(sum(r * r for r in residuals) / len(residuals))
    return {
        "slope": slope,
        "intercept": intercept,
        "correlation": correlation,
        "r_squared": correlation ** 2,
        "rmse": rmse,
        "observations": len(xs),
    }


def bucket_summary(pairs: list[tuple[float, float]], buckets: int) -> list[dict[str, Any]]:
    if len(pairs) < buckets:
        raise SystemExit("Not enough data for bucket evaluation")
    ordered = sorted(pairs, key=lambda item: item[0])
    bucket_size = max(1, len(ordered) // buckets)
    summary: list[dict[str, Any]] = []
    for idx in range(buckets):
        start = idx * bucket_size
        end = len(ordered) if idx == buckets - 1 else min(len(ordered), (idx + 1) * bucket_size)
        bucket = ordered[start:end]
        if not bucket:
            continue
        factor_values = [item[0] for item in bucket]
        returns = [item[1] for item in bucket]
        summary.append({
            "bucket": idx + 1,
            "count": len(bucket),
            "factor_min": min(factor_values),
            "factor_max": max(factor_values),
            "avg_future_return": statistics.mean(returns),
            "median_future_return": statistics.median(returns),
            "hit_rate": len([ret for ret in returns if ret > 0]) / len(returns),
        })
    return summary


def monotonicity_score(values: list[float], direction: str) -> float:
    if len(values) < 2:
        return 0.0
    expected_positive = direction == "positive"
    aligned = 0
    total = 0
    for left, right in zip(values, values[1:]):
        if right == left:
            continue
        total += 1
        if expected_positive and right > left:
            aligned += 1
        if not expected_positive and right < left:
            aligned += 1
    if total == 0:
        return 0.0
    return aligned / total


def detect_runtime() -> dict[str, Any]:
    cpu_count = os.cpu_count() or 1
    mem_total_gb = None
    meminfo = Path("/proc/meminfo")
    if meminfo.exists():
        content = meminfo.read_text(encoding="utf-8", errors="ignore")
        for line in content.splitlines():
            if line.startswith("MemTotal:"):
                parts = line.split()
                if len(parts) >= 2:
                    mem_total_gb = round(int(parts[1]) / 1024 / 1024, 2)
                break

    gpu_available = False
    gpu_info = ""
    if shutil.which("nvidia-smi"):
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                gpu_available = True
                gpu_info = result.stdout.strip().splitlines()[0]
        except Exception:
            gpu_available = False

    if gpu_available:
        profile = "gpu-accelerated"
        recommended_stack = [
            "linear-score",
            "ols-regression",
            "bucket-eval",
            "lead-lag-scan",
            "forward-backtest",
            "optional tree/torch models when external deps are available",
        ]
    elif (mem_total_gb or 0) >= 16 and cpu_count >= 8:
        profile = "balanced-cpu"
        recommended_stack = [
            "linear-score",
            "ols-regression",
            "bucket-eval",
            "lead-lag-scan",
            "forward-backtest",
            "bootstrap/grid-search if needed",
        ]
    else:
        profile = "lightweight-cpu"
        recommended_stack = [
            "linear-score",
            "ols-regression",
            "bucket-eval",
            "lead-lag-scan",
            "forward-backtest",
        ]

    return {
        "profile": profile,
        "cpu_count": cpu_count,
        "mem_total_gb": mem_total_gb,
        "gpu_available": gpu_available,
        "gpu_info": gpu_info,
        "recommended_stack": recommended_stack,
    }


def choose_model_family(
    rows: int,
    features: int,
    horizon: str,
    target_type: str,
    runtime_profile: str,
) -> dict[str, Any]:
    target = target_type.lower()
    short_horizon = horizon in {"h24-48", "d3-7", "w1-2", "w2-4"}

    if rows < 50:
        family = "factor-score + scenario analysis"
        reason = "样本量太小，优先使用稳健的规则打分与情景分析"
    elif target == "continuous" and features <= 12:
        family = "ols-regression + bucket-eval"
        reason = "连续型目标且特征数适中，先用线性解释性模型和分桶对比"
    elif target == "binary":
        family = "threshold score + bucket-eval"
        reason = "当前脚本环境无重型分类器依赖，优先用阈值打分和分桶胜率评估"
    else:
        family = "rank-composite + forward-backtest"
        reason = "数据结构更适合组合评分与收益回放"

    if runtime_profile == "gpu-accelerated" and rows >= 500:
        upgrade = "可升级到树模型 / torch 序列模型，但不应取代当前轻量基线"
    elif runtime_profile == "balanced-cpu" and rows >= 300:
        upgrade = "可升级到更复杂的 CPU 模型或 bootstrap/grid-search"
    else:
        upgrade = "当前以轻量模型为主，不建议切入重型依赖"

    if short_horizon:
        focus = ["relative strength", "turnover pulse", "flow confirmation", "crowding penalty", "lead-lag"]
    else:
        focus = ["quality", "valuation", "macro/liquidity", "earnings trend", "positioning"]

    return {
        "recommended_family": family,
        "reason": reason,
        "upgrade_path": upgrade,
        "focus_factors": focus,
    }


def cmd_detect_runtime(args: argparse.Namespace) -> int:
    payload = OrderedDict(tool="market-alpha-quant-compass/detect-runtime", **detect_runtime())
    write_json(args.output, payload)
    return 0


def cmd_choose_model(args: argparse.Namespace) -> int:
    runtime = detect_runtime()
    payload = OrderedDict(
        tool="market-alpha-quant-compass/choose-model",
        rows=args.rows,
        features=args.features,
        horizon=args.horizon,
        target_type=args.target_type,
        runtime_profile=runtime["profile"],
        **choose_model_family(
            rows=args.rows,
            features=args.features,
            horizon=args.horizon,
            target_type=args.target_type,
            runtime_profile=runtime["profile"],
        ),
    )
    write_json(args.output, payload)
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    rows = read_rows(Path(args.input))
    factors = parse_factor_spec(args.factors)
    usable_rows = []
    factor_values: dict[str, list[float]] = {}

    for factor, _weight in factors:
        values = [to_float(row.get(factor)) for row in rows]
        filtered = [value for value in values if value is not None]
        if not filtered:
            raise SystemExit(f"No numeric values found for factor '{factor}'")
        factor_values[factor] = filtered

    for row in rows:
        score = 0.0
        missing = False
        contributions: dict[str, float] = {}
        for factor, weight in factors:
            raw = to_float(row.get(factor))
            if raw is None:
                missing = True
                break
            contribution = zscore(raw, factor_values[factor]) * weight
            contributions[factor] = round(contribution, 6)
            score += contribution
        if missing:
            continue
        enriched = dict(row)
        enriched["alpha_score"] = round(score, 6)
        enriched["factor_contributions"] = contributions
        usable_rows.append(enriched)

    usable_rows.sort(key=lambda item: item["alpha_score"], reverse=True)
    top_n = usable_rows[: args.top] if args.top else usable_rows
    payload = OrderedDict(
        tool="market-alpha-quant-compass/score",
        input=args.input,
        factors=factors,
        total_rows=len(rows),
        scored_rows=len(usable_rows),
        output_rows=len(top_n),
        rows=top_n,
    )
    write_json(args.output, payload)

    csv_rows = []
    for row in top_n:
        flat = {"ticker": row.get("ticker", ""), "date": row.get("date", ""), "alpha_score": row["alpha_score"]}
        for factor, _weight in factors:
            flat[factor] = row.get(factor, "")
            flat[f"{factor}_contribution"] = row["factor_contributions"].get(factor, "")
        csv_rows.append(flat)
    csv_fields = list(csv_rows[0].keys()) if csv_rows else ["ticker", "alpha_score"]
    companions = maybe_write_companions(
        args.output,
        csv_rows=csv_rows,
        csv_fields=csv_fields,
        png_values=[float(row["alpha_score"]) for row in top_n],
    )
    if companions and args.output:
        payload["companion_outputs"] = companions
        write_json(args.output, payload)
    return 0


def cmd_regress(args: argparse.Namespace) -> int:
    rows = read_rows(Path(args.input))
    xs: list[float] = []
    ys: list[float] = []
    for row in rows:
        x = to_float(row.get(args.x))
        y = to_float(row.get(args.y))
        if x is None or y is None:
            continue
        xs.append(x)
        ys.append(y)
    stats = simple_linear_regression(xs, ys)
    payload = OrderedDict(
        tool="market-alpha-quant-compass/regress",
        input=args.input,
        x=args.x,
        y=args.y,
        **stats,
    )
    if args.predict is not None:
        predict_x = float(args.predict)
        payload["predict_x"] = predict_x
        payload["predict_y"] = stats["intercept"] + stats["slope"] * predict_x
    write_json(args.output, payload)
    return 0


def max_drawdown_from_returns(returns: list[float]) -> float:
    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    for ret in returns:
        equity *= 1.0 + ret
        peak = max(peak, equity)
        dd = (equity / peak) - 1.0
        max_dd = min(max_dd, dd)
    return max_dd


def cmd_backtest(args: argparse.Namespace) -> int:
    rows = read_rows(Path(args.input))
    close_col = args.close_col
    signal_col = args.signal_col
    horizons = [int(item) for item in args.horizons.split(",") if item.strip()]
    closes: list[float] = []
    signals: list[bool] = []
    dates: list[str] = []

    for row in rows:
        close = to_float(row.get(close_col))
        if close is None:
            continue
        closes.append(close)
        dates.append(str(row.get(args.date_col, "")))
        if signal_col:
            signals.append(truthy(row.get(signal_col)))
        else:
            signals.append(True)

    summaries: list[dict[str, Any]] = []
    for horizon in horizons:
        trade_returns: list[float] = []
        trade_dates: list[str] = []
        for idx, (close, active) in enumerate(zip(closes, signals)):
            exit_idx = idx + horizon
            if not active or exit_idx >= len(closes):
                continue
            ret = (closes[exit_idx] / close) - 1.0
            trade_returns.append(ret)
            trade_dates.append(dates[idx] if idx < len(dates) else "")
        if not trade_returns:
            summaries.append({"horizon": horizon, "trades": 0})
            continue
        wins = [ret for ret in trade_returns if ret > 0]
        losses = [ret for ret in trade_returns if ret <= 0]
        avg_win = statistics.mean(wins) if wins else 0.0
        avg_loss = abs(statistics.mean(losses)) if losses else 0.0
        payoff = (avg_win / avg_loss) if avg_loss > 0 else None
        summaries.append({
            "horizon": horizon,
            "trades": len(trade_returns),
            "avg_return": statistics.mean(trade_returns),
            "median_return": statistics.median(trade_returns),
            "hit_rate": len(wins) / len(trade_returns),
            "avg_win": avg_win,
            "avg_loss": -avg_loss if avg_loss > 0 else 0.0,
            "payoff_ratio": payoff,
            "max_drawdown": max_drawdown_from_returns(trade_returns),
            "first_trade": trade_dates[0] if trade_dates else "",
            "last_trade": trade_dates[-1] if trade_dates else "",
        })

    payload = OrderedDict(
        tool="market-alpha-quant-compass/backtest-forward",
        input=args.input,
        close_col=close_col,
        signal_col=signal_col or "",
        horizons=horizons,
        summaries=summaries,
    )
    write_json(args.output, payload)
    csv_fields = [
        "horizon",
        "trades",
        "avg_return",
        "median_return",
        "hit_rate",
        "avg_win",
        "avg_loss",
        "payoff_ratio",
        "max_drawdown",
        "first_trade",
        "last_trade",
    ]
    companions = maybe_write_companions(
        args.output,
        csv_rows=summaries,
        csv_fields=csv_fields,
        png_values=[float(item.get("avg_return", 0.0)) for item in summaries],
    )
    if companions and args.output:
        payload["companion_outputs"] = companions
        write_json(args.output, payload)
    return 0


def cmd_bucket_eval(args: argparse.Namespace) -> int:
    rows = read_rows(Path(args.input))
    pairs = []
    for row in rows:
        factor = to_float(row.get(args.factor))
        future_ret = to_float(row.get(args.future_return))
        if factor is None or future_ret is None:
            continue
        pairs.append((factor, future_ret))
    if len(pairs) < args.buckets:
        raise SystemExit("Not enough data for bucket evaluation")
    summary = bucket_summary(pairs, args.buckets)
    payload = OrderedDict(
        tool="market-alpha-quant-compass/bucket-eval",
        input=args.input,
        factor=args.factor,
        future_return=args.future_return,
        buckets=args.buckets,
        summaries=summary,
    )
    write_json(args.output, payload)
    companions = maybe_write_companions(
        args.output,
        csv_rows=summary,
        csv_fields=["bucket", "count", "factor_min", "factor_max", "avg_future_return", "median_future_return", "hit_rate"],
        png_values=[float(item["avg_future_return"]) for item in summary],
    )
    if companions and args.output:
        payload["companion_outputs"] = companions
        write_json(args.output, payload)
    return 0


def cmd_resonance(args: argparse.Namespace) -> int:
    rows = read_rows(Path(args.input))
    factors = parse_factor_spec(args.factors)
    usable_rows = []
    factor_values: dict[str, list[float]] = {}

    for factor, _weight in factors:
        values = [to_float(row.get(factor)) for row in rows]
        filtered = [value for value in values if value is not None]
        if not filtered:
            raise SystemExit(f"No numeric values found for factor '{factor}'")
        factor_values[factor] = filtered

    for row in rows:
        resonance_score = 0.0
        aligned = 0
        conflicting = 0
        missing = False
        contributions: dict[str, float] = {}
        for factor, weight in factors:
            raw = to_float(row.get(factor))
            if raw is None:
                missing = True
                break
            contribution = zscore(raw, factor_values[factor]) * weight
            contributions[factor] = round(contribution, 6)
            resonance_score += contribution
            if contribution >= args.threshold:
                aligned += 1
            elif contribution <= -args.threshold:
                conflicting += 1
        if missing:
            continue
        enriched = dict(row)
        enriched["resonance_score"] = round(resonance_score, 6)
        enriched["aligned_factors"] = aligned
        enriched["conflicting_factors"] = conflicting
        enriched["alignment_ratio"] = round(aligned / len(factors), 6) if factors else 0.0
        enriched["factor_contributions"] = contributions
        usable_rows.append(enriched)

    usable_rows.sort(
        key=lambda item: (
            float(item["resonance_score"]),
            int(item["aligned_factors"]),
            -int(item["conflicting_factors"]),
        ),
        reverse=True,
    )
    top_n = usable_rows[: args.top] if args.top else usable_rows
    payload = OrderedDict(
        tool="market-alpha-quant-compass/resonance",
        input=args.input,
        factors=factors,
        threshold=args.threshold,
        total_rows=len(rows),
        scored_rows=len(usable_rows),
        output_rows=len(top_n),
        rows=top_n,
    )
    write_json(args.output, payload)
    csv_rows = []
    for row in top_n:
        flat = {
            "ticker": row.get("ticker", ""),
            "date": row.get("date", ""),
            "resonance_score": row["resonance_score"],
            "aligned_factors": row["aligned_factors"],
            "conflicting_factors": row["conflicting_factors"],
            "alignment_ratio": row["alignment_ratio"],
        }
        for factor, _weight in factors:
            flat[factor] = row.get(factor, "")
            flat[f"{factor}_contribution"] = row["factor_contributions"].get(factor, "")
        csv_rows.append(flat)
    csv_fields = list(csv_rows[0].keys()) if csv_rows else ["ticker", "resonance_score"]
    companions = maybe_write_companions(
        args.output,
        csv_rows=csv_rows,
        csv_fields=csv_fields,
        png_values=[float(row["resonance_score"]) for row in top_n],
    )
    if companions and args.output:
        payload["companion_outputs"] = companions
        write_json(args.output, payload)
    return 0


def cmd_factor_mine(args: argparse.Namespace) -> int:
    rows = read_rows(Path(args.input))
    exclude = {"ticker", "date", "symbol", "name", "close", "price", "signal", args.target.lower()}
    factors = parse_factor_names(args.factors) if args.factors else numeric_column_names(rows, exclude=exclude)
    if not factors:
        raise SystemExit("No factor columns available for mining")

    mined: list[dict[str, Any]] = []
    for factor in factors:
        pairs = []
        for row in rows:
            factor_value = to_float(row.get(factor))
            target_value = to_float(row.get(args.target))
            if factor_value is None or target_value is None:
                continue
            pairs.append((factor_value, target_value))
        if len(pairs) < args.min_obs:
            continue
        xs = [item[0] for item in pairs]
        ys = [item[1] for item in pairs]
        stats = simple_linear_regression(xs, ys)
        buckets = bucket_summary(pairs, args.buckets)
        avg_returns = [float(item["avg_future_return"]) for item in buckets]
        direction = "positive" if stats["correlation"] >= 0 else "negative"
        bucket_spread = avg_returns[-1] - avg_returns[0]
        mined.append({
            "factor": factor,
            "observations": len(pairs),
            "correlation": stats["correlation"],
            "abs_correlation": abs(stats["correlation"]),
            "r_squared": stats["r_squared"],
            "slope": stats["slope"],
            "direction": direction,
            "bucket_spread": bucket_spread,
            "abs_bucket_spread": abs(bucket_spread),
            "monotonicity": monotonicity_score(avg_returns, direction=direction),
            "bucket_summary": buckets,
        })

    if not mined:
        raise SystemExit("No factor met the minimum observation threshold")

    corr_values = [item["abs_correlation"] for item in mined]
    spread_values = [item["abs_bucket_spread"] for item in mined]
    for item in mined:
        corr_component = zscore(float(item["abs_correlation"]), corr_values) if len(corr_values) > 1 else 0.0
        spread_component = zscore(float(item["abs_bucket_spread"]), spread_values) if len(spread_values) > 1 else 0.0
        item["mine_score"] = round(corr_component * 0.45 + spread_component * 0.35 + float(item["monotonicity"]) * 0.20, 6)

    mined.sort(key=lambda item: float(item["mine_score"]), reverse=True)
    top_n = mined[: args.top] if args.top else mined
    payload = OrderedDict(
        tool="market-alpha-quant-compass/factor-mine",
        input=args.input,
        target=args.target,
        buckets=args.buckets,
        min_obs=args.min_obs,
        factor_count=len(mined),
        factors=top_n,
    )
    write_json(args.output, payload)
    csv_rows = [
        {
            "factor": item["factor"],
            "mine_score": item["mine_score"],
            "observations": item["observations"],
            "direction": item["direction"],
            "correlation": item["correlation"],
            "r_squared": item["r_squared"],
            "bucket_spread": item["bucket_spread"],
            "monotonicity": item["monotonicity"],
        }
        for item in top_n
    ]
    companions = maybe_write_companions(
        args.output,
        csv_rows=csv_rows,
        csv_fields=["factor", "mine_score", "observations", "direction", "correlation", "r_squared", "bucket_spread", "monotonicity"],
        png_values=[float(item["mine_score"]) for item in top_n],
    )
    if companions and args.output:
        payload["companion_outputs"] = companions
        write_json(args.output, payload)
    return 0


def cmd_lead_lag_scan(args: argparse.Namespace) -> int:
    rows = read_rows(Path(args.input))
    xs: list[float] = []
    ys: list[float] = []
    for row in rows:
        x = to_float(row.get(args.x))
        y = to_float(row.get(args.y))
        if x is None or y is None:
            continue
        xs.append(x)
        ys.append(y)
    if len(xs) < 3 or len(ys) < 3:
        raise SystemExit("Need at least 3 observations for lead-lag scan")

    results = []
    for lag in range(0, args.max_lag + 1):
        if lag >= len(xs):
            break
        shifted_x = xs[: len(xs) - lag] if lag > 0 else xs[:]
        shifted_y = ys[lag:] if lag > 0 else ys[:]
        if len(shifted_x) < 2 or len(shifted_y) < 2:
            continue
        stats = simple_linear_regression(shifted_x, shifted_y)
        results.append({
            "lag": lag,
            "correlation": stats["correlation"],
            "r_squared": stats["r_squared"],
            "slope": stats["slope"],
            "observations": stats["observations"],
        })
    results.sort(key=lambda item: abs(item["correlation"]), reverse=True)
    payload = OrderedDict(
        tool="market-alpha-quant-compass/lead-lag-scan",
        input=args.input,
        x=args.x,
        y=args.y,
        max_lag=args.max_lag,
        best=results[0] if results else {},
        results=results,
    )
    write_json(args.output, payload)
    companions = maybe_write_companions(
        args.output,
        csv_rows=results,
        csv_fields=["lag", "correlation", "r_squared", "slope", "observations"],
        png_values=[float(item["correlation"]) for item in sorted(results, key=lambda item: item["lag"])],
    )
    if companions and args.output:
        payload["companion_outputs"] = companions
        write_json(args.output, payload)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Simple quant compass for market-alpha tasks")
    subparsers = parser.add_subparsers(dest="command", required=True)

    detect = subparsers.add_parser("detect-runtime")
    detect.add_argument("--output")
    detect.set_defaults(func=cmd_detect_runtime)

    choose = subparsers.add_parser("choose-model")
    choose.add_argument("--rows", type=int, required=True)
    choose.add_argument("--features", type=int, required=True)
    choose.add_argument("--horizon", required=True)
    choose.add_argument("--target-type", default="continuous")
    choose.add_argument("--output")
    choose.set_defaults(func=cmd_choose_model)

    score = subparsers.add_parser("score")
    score.add_argument("--input", required=True)
    score.add_argument("--factors", required=True, help="comma-separated factor:weight pairs")
    score.add_argument("--top", type=int, default=0)
    score.add_argument("--output")
    score.set_defaults(func=cmd_score)

    regress = subparsers.add_parser("regress")
    regress.add_argument("--input", required=True)
    regress.add_argument("--x", required=True)
    regress.add_argument("--y", required=True)
    regress.add_argument("--predict")
    regress.add_argument("--output")
    regress.set_defaults(func=cmd_regress)

    backtest = subparsers.add_parser("backtest-forward")
    backtest.add_argument("--input", required=True)
    backtest.add_argument("--close-col", default="close")
    backtest.add_argument("--signal-col")
    backtest.add_argument("--date-col", default="date")
    backtest.add_argument("--horizons", default="1,2,3,5")
    backtest.add_argument("--output")
    backtest.set_defaults(func=cmd_backtest)

    bucket = subparsers.add_parser("bucket-eval")
    bucket.add_argument("--input", required=True)
    bucket.add_argument("--factor", required=True)
    bucket.add_argument("--future-return", required=True)
    bucket.add_argument("--buckets", type=int, default=5)
    bucket.add_argument("--output")
    bucket.set_defaults(func=cmd_bucket_eval)

    lag = subparsers.add_parser("lead-lag-scan")
    lag.add_argument("--input", required=True)
    lag.add_argument("--x", required=True)
    lag.add_argument("--y", required=True)
    lag.add_argument("--max-lag", type=int, default=5)
    lag.add_argument("--output")
    lag.set_defaults(func=cmd_lead_lag_scan)

    resonance = subparsers.add_parser("resonance")
    resonance.add_argument("--input", required=True)
    resonance.add_argument("--factors", required=True, help="comma-separated factor:weight pairs")
    resonance.add_argument("--threshold", type=float, default=0.25)
    resonance.add_argument("--top", type=int, default=0)
    resonance.add_argument("--output")
    resonance.set_defaults(func=cmd_resonance)

    factor_mine = subparsers.add_parser("factor-mine")
    factor_mine.add_argument("--input", required=True)
    factor_mine.add_argument("--target", required=True)
    factor_mine.add_argument("--factors", default="")
    factor_mine.add_argument("--buckets", type=int, default=5)
    factor_mine.add_argument("--min-obs", type=int, default=10)
    factor_mine.add_argument("--top", type=int, default=0)
    factor_mine.add_argument("--output")
    factor_mine.set_defaults(func=cmd_factor_mine)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
