#!/usr/bin/env python3
"""
Geo Sentinel — Forecast Engine v3
F-G+ forecasting: LLM scenario reasoning constrained by base rates, decomposition,
counter-evidence, prior-aware recalibration, and lightweight uncertainty bounds.

Usage:
  python3 forecast_engine.py --input intel.json --output forecast.json [--max-iter 3] [--threshold 0.03]
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from statistics import median
from typing import Any

EPS = 1e-6
DEFAULT_SHARED_INFORMATION_RISK = 0.35
TAIL_SIGNAL_FLOOR = 0.20
TAIL_ANALOGUE_FLOOR = 0.20

SIGMA_TABLE = {
    "military_conflict_escalation": 0.15,
    "election_outcomes": 0.10,
    "policy_regulation_changes": 0.12,
    "trade_economic_decisions": 0.08,
    "diplomatic_negotiations": 0.13,
    "regime_change": 0.18,
    "market_moving_events": 0.11,
    "default": 0.14,
}

DEFAULT_ALPHA = 0.40
DEFAULT_BETA = 0.35
DEFAULT_GAMMA = 0.15
DEFAULT_DELTA = 0.10
SIGNAL_SCALE = 1.60
ANALOGUE_SCALE = 1.20


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def clamp_prob(value: Any, default: float = 0.5) -> float:
    try:
        prob = float(value)
    except (TypeError, ValueError):
        prob = default
    return min(max(prob, EPS), 1.0 - EPS)


def clamp_unit(value: Any, default: float = 0.0) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        score = default
    return min(max(score, 0.0), 1.0)


def clamp_signed(value: float) -> float:
    return min(max(value, -1.0), 1.0)


def safe_logit(prob: float) -> float:
    prob = clamp_prob(prob)
    return math.log(prob / (1.0 - prob))


def safe_sigmoid(value: float) -> float:
    if value >= 0:
        exp_neg = math.exp(-value)
        return 1.0 / (1.0 + exp_neg)
    exp_pos = math.exp(value)
    return exp_pos / (1.0 + exp_pos)


def normalize(probs: list[float]) -> list[float]:
    if not probs:
        return []
    safe_probs = [max(clamp_prob(prob), EPS) for prob in probs]
    total = sum(safe_probs)
    if total <= 0:
        return [1.0 / len(safe_probs)] * len(safe_probs)
    return [prob / total for prob in safe_probs]


def aggregate_llm_probabilities(scenario: dict[str, Any], fallback: float) -> dict[str, Any]:
    raw = scenario.get("llm_probabilities")
    values: list[float] = []
    if isinstance(raw, list):
        for item in raw:
            try:
                values.append(clamp_prob(item))
            except Exception:
                continue
    if not values:
        for key in ("llm_probability", "probability", "initial_probability"):
            if key in scenario:
                values = [clamp_prob(scenario.get(key))]
                break
    if not values:
        values = [clamp_prob(fallback)]

    center = median(values)
    avg = sum(values) / len(values)
    dispersion = sum(abs(value - center) for value in values) / len(values)
    skew = avg - center
    return {
        "values": values,
        "center": center,
        "mean": avg,
        "dispersion": dispersion,
        "skew": skew,
        "count": len(values),
    }


def get_global_signal_lists(data: dict[str, Any]) -> tuple[list[Any], list[Any]]:
    signals = data.get("signals", {})
    supporting = signals.get("supporting", [])
    contradicting = signals.get("contradicting", [])
    return supporting if isinstance(supporting, list) else [], contradicting if isinstance(contradicting, list) else []


def get_scenario_signal_lists(
    scenario: dict[str, Any],
    global_supporting: list[Any],
    global_contradicting: list[Any],
) -> tuple[list[Any], list[Any]]:
    supporting = scenario.get("supporting_signals")
    contradicting = scenario.get("contradicting_signals")
    supporting_list = supporting if isinstance(supporting, list) else global_supporting
    contradicting_list = contradicting if isinstance(contradicting, list) else global_contradicting
    return supporting_list, contradicting_list


def compute_signal_score(n_supporting: int, n_contradicting: int) -> float:
    total = n_supporting + n_contradicting
    if total == 0:
        return 0.0
    balance = (n_supporting - n_contradicting) / total
    magnitude = min(total / 6.0, 1.0)
    return clamp_signed(balance * (0.5 + 0.5 * magnitude))


def compute_analogue_score(raw: Any) -> tuple[float, float]:
    if raw is None:
        return 0.0, 0.0
    if isinstance(raw, (int, float)):
        return clamp_signed(float(raw)), 0.5
    if not isinstance(raw, list) or not raw:
        return 0.0, 0.0

    weighted_sum = 0.0
    weight_sum = 0.0
    for item in raw:
        if isinstance(item, dict):
            weight = clamp_unit(item.get("similarity", item.get("weight", 0.5)), default=0.5)
            score = item.get("score")
            if score is not None:
                signed = clamp_signed(float(score))
            else:
                direction = str(item.get("direction", "supports")).strip().lower()
                signed = -1.0 if direction in {"contradicts", "against", "negative"} else 1.0
            weighted_sum += signed * weight
            weight_sum += weight
        elif isinstance(item, (int, float)):
            signed = clamp_signed(float(item))
            weight = abs(signed)
            weighted_sum += signed * max(weight, 0.1)
            weight_sum += max(weight, 0.1)

    if weight_sum <= 0:
        return 0.0, 0.0
    score = clamp_signed(weighted_sum / weight_sum)
    confidence = min(weight_sum / max(len(raw), 1), 1.0)
    return score, confidence


def scenario_base_rate(scenario: dict[str, Any], historical: dict[str, Any], scenario_count: int) -> float:
    if "base_rate" in scenario:
        return clamp_prob(scenario.get("base_rate"))

    scenario_map = historical.get("scenario_base_rates", {})
    if isinstance(scenario_map, dict):
        scenario_id = str(scenario.get("id", "")).strip()
        if scenario_id and scenario_id in scenario_map:
            return clamp_prob(scenario_map.get(scenario_id))

    if "base_rate" in historical:
        return clamp_prob(float(historical.get("base_rate")) / max(scenario_count, 1), default=1.0 / max(scenario_count, 1))

    return clamp_prob(1.0 / max(scenario_count, 1))


def scenario_anchor(scenario: dict[str, Any], historical: dict[str, Any], base_rate: float) -> float:
    for key in ("meta_prior", "estimated_prior", "prior_estimate"):
        if key in scenario:
            return clamp_prob(scenario.get(key), default=base_rate)

    prior_map = historical.get("prior_by_scenario", {})
    if isinstance(prior_map, dict):
        scenario_id = str(scenario.get("id", "")).strip()
        if scenario_id and scenario_id in prior_map:
            return clamp_prob(prior_map.get(scenario_id), default=base_rate)

    return clamp_prob(base_rate)


def reference_quality(scenario: dict[str, Any], historical: dict[str, Any]) -> float:
    if "reference_class_quality" in scenario:
        return clamp_unit(scenario.get("reference_class_quality"), default=0.5)

    size_value = scenario.get("reference_class_size", historical.get("reference_class_size", 0))
    try:
        size = max(float(size_value), 0.0)
    except (TypeError, ValueError):
        size = 0.0
    if size <= 0:
        return 0.20
    return min(math.log1p(size) / math.log(21.0), 1.0)


def recalibrate_around_anchor(prob: float, anchor: float, gamma: float) -> float:
    prob = clamp_prob(prob)
    anchor = clamp_prob(anchor)
    adjusted = safe_logit(anchor) + gamma * (safe_logit(prob) - safe_logit(anchor))
    return clamp_prob(safe_sigmoid(adjusted))


def apply_tail_discipline(prob: float, base_rate: float, llm_center: float, signal_score: float, analogue_score: float) -> float:
    if base_rate >= 0.10 or signal_score >= TAIL_SIGNAL_FLOOR or analogue_score >= TAIL_ANALOGUE_FLOOR:
        return clamp_prob(prob)
    soft_cap = max(base_rate * 3.0, llm_center * 1.15, 0.02)
    return clamp_prob(min(prob, min(soft_cap, 0.35)))


def compute_gamma(
    llm_stats: dict[str, Any],
    contrarian_bonus: float,
    reference_q: float,
    shared_information_risk: float,
) -> float:
    diversity_bonus = min(llm_stats["dispersion"] * 2.5, 0.25) + min(abs(llm_stats["skew"]) * 2.0, 0.10)
    gamma = 1.0 + diversity_bonus + contrarian_bonus + 0.10 * (reference_q - 0.50) - 0.35 * shared_information_risk
    return min(max(gamma, 0.85), 1.35)


def compute_sigma(
    category: str,
    n_contradicting: int,
    t_days: int,
    llm_stats: dict[str, Any],
    shared_information_risk: float,
    reference_q: float,
) -> float:
    sigma_base = SIGMA_TABLE.get(category, SIGMA_TABLE["default"])
    sigma = sigma_base
    sigma *= 1.0 + 0.05 * n_contradicting
    sigma *= 1.0 + 0.004 * max(t_days, 0)
    sigma *= 1.0 + 1.50 * llm_stats["dispersion"]
    sigma *= 1.0 + 0.50 * shared_information_risk
    sigma *= 1.0 + 0.50 * (1.0 - reference_q)
    return sigma


def compute_ci(prob: float, sigma: float) -> tuple[float, float]:
    ci_half = min(0.35, 1.96 * sigma * 0.45)
    return max(0.0, prob - ci_half), min(1.0, prob + ci_half)


def contrarian_bonus(
    scenario: dict[str, Any],
    llm_stats: dict[str, Any],
    signal_score: float,
    analogue_score: float,
) -> float:
    bonus = 0.0
    if scenario.get("contrarian_signal"):
        bonus += 0.10
    if llm_stats["count"] >= 3 and llm_stats["dispersion"] >= 0.08:
        bonus += 0.08
    if signal_score > 0.20 and analogue_score > 0.15:
        bonus += 0.05
    return min(bonus, 0.20)


def blended_probability(base_rate: float, llm_center: float, signal_score: float, analogue_score: float) -> float:
    logit_mix = (
        DEFAULT_ALPHA * safe_logit(base_rate)
        + DEFAULT_BETA * safe_logit(llm_center)
        + DEFAULT_GAMMA * SIGNAL_SCALE * signal_score
        + DEFAULT_DELTA * ANALOGUE_SCALE * analogue_score
    )
    return clamp_prob(safe_sigmoid(logit_mix))


def run_engine(data: dict[str, Any], max_iter: int = 3, threshold: float = 0.03) -> dict[str, Any]:
    topic = str(data.get("topic", "")).strip() or "forecast-topic"
    t_days = int(data.get("time_horizon_days", 30))
    scenarios = data.get("scenarios", [])
    historical = data.get("historical", {})
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("Input must include a non-empty 'scenarios' list")

    category = str(historical.get("event_category", "default")).strip() or "default"
    shared_information_risk = clamp_unit(data.get("shared_information_risk", DEFAULT_SHARED_INFORMATION_RISK), DEFAULT_SHARED_INFORMATION_RISK)
    global_supporting, global_contradicting = get_global_signal_lists(data)
    scenario_count = len(scenarios)

    scenario_meta: list[dict[str, Any]] = []
    initial_probs: list[float] = []
    for scenario in scenarios:
        base_rate = scenario_base_rate(scenario, historical, scenario_count)
        llm_stats = aggregate_llm_probabilities(scenario, fallback=base_rate)
        scenario_meta.append(
            {
                "base_rate": base_rate,
                "llm_stats": llm_stats,
                "drivers": scenario.get("drivers", []),
                "disruptors": scenario.get("disruptors", []),
                "watch_signals": scenario.get("watch_signals", []),
            }
        )
        initial_probs.append(llm_stats["center"])

    working_probs = normalize(initial_probs)
    prev_probs: list[float] | None = None
    scenario_debug: list[dict[str, Any]] = []
    converged = False
    iterations = 0

    for iteration in range(1, max_iter + 1):
        iterations = iteration
        raw_probs: list[float] = []
        current_debug: list[dict[str, Any]] = []

        for index, scenario in enumerate(scenarios):
            meta = scenario_meta[index]
            base_rate = meta["base_rate"]
            llm_stats = meta["llm_stats"]
            llm_center = clamp_prob(0.5 * llm_stats["center"] + 0.5 * working_probs[index])
            supporting, contradicting = get_scenario_signal_lists(scenario, global_supporting, global_contradicting)
            signal_score = compute_signal_score(len(supporting), len(contradicting))
            analogue_score, analogue_confidence = compute_analogue_score(scenario.get("analogues"))
            reference_q = reference_quality(scenario, historical)
            anchor = scenario_anchor(scenario, historical, base_rate)
            contra_bonus = contrarian_bonus(scenario, llm_stats, signal_score, analogue_score)
            gamma = compute_gamma(llm_stats, contra_bonus, reference_q, shared_information_risk)

            mixed = blended_probability(base_rate, llm_center, signal_score, analogue_score)
            recalibrated = recalibrate_around_anchor(mixed, anchor, gamma)
            recalibrated = apply_tail_discipline(recalibrated, base_rate, llm_center, signal_score, analogue_score)
            sigma = compute_sigma(category, len(contradicting), t_days, llm_stats, shared_information_risk, reference_q)

            raw_probs.append(recalibrated)
            current_debug.append(
                {
                    "base_rate": round(base_rate, 4),
                    "anchor": round(anchor, 4),
                    "llm_center": round(llm_center, 4),
                    "llm_dispersion": round(llm_stats["dispersion"], 4),
                    "signal_score": round(signal_score, 4),
                    "analogue_score": round(analogue_score, 4),
                    "analogue_confidence": round(analogue_confidence, 4),
                    "reference_quality": round(reference_q, 4),
                    "gamma": round(gamma, 4),
                    "sigma": round(sigma, 4),
                }
            )

        normed = normalize(raw_probs)
        if prev_probs is not None:
            max_delta = max(abs(a - b) for a, b in zip(normed, prev_probs))
            if max_delta < threshold:
                working_probs = normed
                scenario_debug = current_debug
                converged = True
                break

        prev_probs = working_probs
        working_probs = normed
        scenario_debug = current_debug

    if not converged and iterations >= 2:
        max_delta = max(abs(a - b) for a, b in zip(working_probs, prev_probs or working_probs))
        converged = max_delta < threshold

    output_scenarios: list[dict[str, Any]] = []
    for index, scenario in enumerate(scenarios):
        debug = scenario_debug[index]
        probability = clamp_prob(working_probs[index])
        ci_lower, ci_upper = compute_ci(probability, float(debug["sigma"]))
        output_scenarios.append(
            {
                "id": scenario.get("id", f"S{index + 1}"),
                "title": scenario.get("title", f"Scenario {index + 1}"),
                "description": scenario.get("description", ""),
                "probability": round(probability, 4),
                "ci_lower": round(ci_lower, 4),
                "ci_upper": round(ci_upper, 4),
                "drivers": scenario_meta[index]["drivers"],
                "disruptors": scenario_meta[index]["disruptors"],
                "watch_signals": scenario_meta[index]["watch_signals"],
                "calibration": debug,
            }
        )

    output_scenarios.sort(key=lambda item: item["probability"], reverse=True)

    if converged and iterations <= 2:
        confidence = "high"
    elif converged:
        confidence = "moderate"
    else:
        confidence = "low"

    return {
        "topic": topic,
        "analysis_date": utc_now_iso(),
        "time_horizon_days": t_days,
        "scenarios": output_scenarios,
        "iterations": iterations,
        "convergence": converged,
        "confidence_level": confidence,
        "key_uncertainties": data.get("key_uncertainties", []),
        "model_parameters": {
            "alpha": DEFAULT_ALPHA,
            "beta": DEFAULT_BETA,
            "gamma": DEFAULT_GAMMA,
            "delta": DEFAULT_DELTA,
            "signal_scale": SIGNAL_SCALE,
            "analogue_scale": ANALOGUE_SCALE,
            "shared_information_risk": round(shared_information_risk, 4),
            "event_category": category,
            "threshold": threshold,
            "max_iter": max_iter,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Geo Sentinel Forecast Engine v3")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-iter", type=int, default=3)
    parser.add_argument("--threshold", type=float, default=0.03)
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as handle:
        payload = json.load(handle)

    result = run_engine(payload, max_iter=args.max_iter, threshold=args.threshold)

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(f"[OK] convergence={result['convergence']}, iterations={result['iterations']}, confidence={result['confidence_level']}")
    for scenario in result["scenarios"]:
        print(
            f"  {scenario['id']}: {scenario['title'][:40]:40s} -> "
            f"{scenario['probability']:.1%} [{scenario['ci_lower']:.1%}, {scenario['ci_upper']:.1%}]"
        )


if __name__ == "__main__":
    main()
