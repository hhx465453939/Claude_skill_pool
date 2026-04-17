#!/usr/bin/env python3
"""
Deep Research 轻量量化工具箱

目标：
- 在无 numpy / pandas 的环境下也能完成基础数值核验
- 支持 FRED 固定公开数据抓取
- 支持 CSV 描述统计、简单线性回归、表达式计算
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import math
from collections import OrderedDict
from pathlib import Path
from statistics import mean, median, stdev
from typing import Any

import requests
from requests import RequestException


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def parse_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if math.isnan(value) or math.isinf(value):
            return None
        return float(value)

    text = str(value).strip().replace(",", "")
    if text in {"", ".", "NA", "N/A", "null", "None"}:
        return None

    try:
        number = float(text)
    except ValueError:
        return None

    if math.isnan(number) or math.isinf(number):
        return None
    return number


def output_result(payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    for key, value in payload.items():
        if isinstance(value, (dict, list)):
            print(f"{key}={json.dumps(value, ensure_ascii=False)}")
        else:
            print(f"{key}={value}")


def cmd_fetch_fred(args: argparse.Namespace) -> int:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={args.series}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except RequestException as exc:
        raise SystemExit(
            "FRED fetch failed. Check outbound network/proxy access in the current runtime, "
            f"or manually download the CSV first. Source URL: {url}. Error: {exc}"
        ) from exc

    rows: list[dict[str, str]] = []
    reader = csv.DictReader(response.text.splitlines())
    for row in reader:
        date = row.get("DATE", "")
        value = row.get(args.series, "")

        if args.start and date < args.start:
            continue
        if args.end and date > args.end:
            continue

        rows.append({"date": date, "value": value})

    if args.output:
        output_path = Path(args.output)
        ensure_parent(output_path)
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["date", "value"])
            writer.writeheader()
            writer.writerows(rows)

    payload = OrderedDict(
        tool="fetch-fred",
        series=args.series,
        row_count=len(rows),
        start=args.start or (rows[0]["date"] if rows else ""),
        end=args.end or (rows[-1]["date"] if rows else ""),
        output=args.output or "",
        source_url=url,
    )
    output_result(payload, args.json)
    return 0


def load_csv_rows(file_path: Path) -> list[dict[str, str]]:
    with file_path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def get_numeric_series(rows: list[dict[str, str]], column: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = parse_number(row.get(column))
        if value is not None:
            values.append(value)
    return values


def cmd_describe(args: argparse.Namespace) -> int:
    rows = load_csv_rows(Path(args.input))
    values = get_numeric_series(rows, args.column)
    if len(values) < 1:
        raise SystemExit(f"No numeric values found in column: {args.column}")

    payload = OrderedDict(
        tool="describe",
        input=args.input,
        column=args.column,
        count=len(values),
        mean=mean(values),
        median=median(values),
        min=min(values),
        max=max(values),
        sum=sum(values),
        stdev=stdev(values) if len(values) > 1 else 0.0,
    )
    output_result(payload, args.json)
    return 0


def simple_linear_regression(xs: list[float], ys: list[float]) -> dict[str, float]:
    if len(xs) != len(ys):
        raise ValueError("x and y length mismatch")
    if len(xs) < 2:
        raise ValueError("need at least 2 points")

    x_bar = mean(xs)
    y_bar = mean(ys)
    sxx = sum((x - x_bar) ** 2 for x in xs)
    sxy = sum((x - x_bar) * (y - y_bar) for x, y in zip(xs, ys))
    syy = sum((y - y_bar) ** 2 for y in ys)

    if sxx == 0:
        raise ValueError("x has zero variance")

    slope = sxy / sxx
    intercept = y_bar - slope * x_bar
    correlation = 0.0 if syy == 0 else sxy / math.sqrt(sxx * syy)
    r_squared = correlation ** 2

    residuals = [y - (intercept + slope * x) for x, y in zip(xs, ys)]
    rmse = math.sqrt(sum(r * r for r in residuals) / len(residuals))

    return {
        "slope": slope,
        "intercept": intercept,
        "correlation": correlation,
        "r_squared": r_squared,
        "rmse": rmse,
        "n": float(len(xs)),
    }


def cmd_regress(args: argparse.Namespace) -> int:
    rows = load_csv_rows(Path(args.input))
    pairs: list[tuple[float, float]] = []
    for row in rows:
        x_val = parse_number(row.get(args.x))
        y_val = parse_number(row.get(args.y))
        if x_val is None or y_val is None:
            continue
        pairs.append((x_val, y_val))

    if len(pairs) < 2:
        raise SystemExit("Not enough paired numeric rows for regression")

    xs = [pair[0] for pair in pairs]
    ys = [pair[1] for pair in pairs]
    stats = simple_linear_regression(xs, ys)
    payload: dict[str, Any] = OrderedDict(
        tool="regress",
        input=args.input,
        x=args.x,
        y=args.y,
        observations=len(pairs),
        slope=stats["slope"],
        intercept=stats["intercept"],
        correlation=stats["correlation"],
        r_squared=stats["r_squared"],
        rmse=stats["rmse"],
    )

    if args.predict is not None:
        x_value = float(args.predict)
        payload["predict_x"] = x_value
        payload["predict_y"] = stats["intercept"] + stats["slope"] * x_value

    output_result(payload, args.json)
    return 0


ALLOWED_AST_NODES = {
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.Mod,
    ast.USub,
    ast.UAdd,
    ast.Load,
    ast.Name,
    ast.Constant,
}


def safe_eval(expr: str, variables: dict[str, float]) -> float:
    tree = ast.parse(expr, mode="eval")
    for node in ast.walk(tree):
        if type(node) not in ALLOWED_AST_NODES:
            raise ValueError(f"Unsupported expression node: {type(node).__name__}")

    compiled = compile(tree, "<calc>", "eval")
    return float(eval(compiled, {"__builtins__": {}}, variables))


def cmd_calc(args: argparse.Namespace) -> int:
    variables: dict[str, float] = {}
    for item in args.var or []:
        key, _, raw_value = item.partition("=")
        if not key or not raw_value:
            raise SystemExit(f"Invalid --var entry: {item}")
        variables[key] = float(raw_value)

    result = safe_eval(args.expr, variables)
    payload = OrderedDict(
        tool="calc",
        expression=args.expr,
        variables=variables,
        result=result,
    )
    output_result(payload, args.json)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deep Research lightweight quantitative toolkit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    fred = subparsers.add_parser("fetch-fred", help="Fetch a FRED series into CSV")
    fred.add_argument("--series", required=True, help="FRED series id, e.g. FEDFUNDS")
    fred.add_argument("--start", help="Inclusive start date YYYY-MM-DD")
    fred.add_argument("--end", help="Inclusive end date YYYY-MM-DD")
    fred.add_argument("--output", help="Output CSV path")
    fred.add_argument("--json", action="store_true", help="Print JSON output")
    fred.set_defaults(func=cmd_fetch_fred)

    describe = subparsers.add_parser("describe", help="Run descriptive stats for a CSV column")
    describe.add_argument("--input", required=True, help="CSV file path")
    describe.add_argument("--column", required=True, help="Numeric column name")
    describe.add_argument("--json", action="store_true", help="Print JSON output")
    describe.set_defaults(func=cmd_describe)

    regress = subparsers.add_parser("regress", help="Run simple linear regression y ~ x from CSV")
    regress.add_argument("--input", required=True, help="CSV file path")
    regress.add_argument("--x", required=True, help="Independent variable column")
    regress.add_argument("--y", required=True, help="Dependent variable column")
    regress.add_argument("--predict", help="Optional x value for prediction")
    regress.add_argument("--json", action="store_true", help="Print JSON output")
    regress.set_defaults(func=cmd_regress)

    calc = subparsers.add_parser("calc", help="Evaluate a simple numeric expression")
    calc.add_argument("--expr", required=True, help='Expression such as "(a-b)/b*100"')
    calc.add_argument("--var", action="append", help="Variable assignment like a=12")
    calc.add_argument("--json", action="store_true", help="Print JSON output")
    calc.set_defaults(func=cmd_calc)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
