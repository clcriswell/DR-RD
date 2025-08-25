from __future__ import annotations

import streamlit as st

from app.price_loader import cost_usd, load_prices
from app.ui_presets import UI_PRESETS
from core.llm import select_model


def _estimate_remaining(plan: dict | list | None, stage_counts: dict[str, int]) -> float:
    cfg = st.session_state.get("MODE_CFG", {}) or {}
    models = cfg.get("models", {})
    weights = cfg.get("stage_weights", {})
    target = cfg.get("target_cost_usd", 0.0)
    preset = UI_PRESETS.get("standard", {})
    refinement_rounds = preset.get("refinement_rounds", 1)
    if isinstance(plan, dict):
        roles = len(plan.keys())
    elif isinstance(plan, list):
        roles = len({t.get("role") for t in plan})
    else:
        roles = 6  # assume one task per core role if unknown
    expected_calls = {"plan": 1, "exec": roles * refinement_rounds, "synth": 1}
    prices = load_prices()
    remainder = 0.0
    for stage, calls in expected_calls.items():
        remaining = calls - stage_counts.get(stage, 0)
        if remaining <= 0:
            continue
        model = models.get(
            stage,
            models.get("exec", models.get("plan", select_model("agent"))),
        )
        weight = weights.get(stage, 0.0)
        stage_budget = target * weight
        per_call_budget = stage_budget / calls if calls else 0.0
        p = prices.get(model, prices.get("default", {}))
        denom = p.get("in_per_1k", 0.0) + p.get("out_per_1k", 0.0)
        if denom <= 0:
            continue
        total_tokens = 2 * 1000 * per_call_budget / denom
        pt = ct = total_tokens / 2
        remainder += remaining * cost_usd(model, pt, ct)
    return remainder


def render_estimator(idea_text: str):
    st.subheader("Run Cost Estimate")
    est_cost = _estimate_remaining(None, {})
    metric = getattr(st, "metric", None)
    if callable(metric):
        metric("Estimated Cost", f"${est_cost:.2f}")


def render_cost_summary(plan: dict | list | None):
    log = st.session_state.get("usage_log", [])
    actual = 0.0
    stage_counts: dict[str, int] = {}
    for entry in log:
        actual += cost_usd(entry["model"], entry["pt"], entry["ct"])
        stage_counts[entry["stage"]] = stage_counts.get(entry["stage"], 0) + 1
    remainder = _estimate_remaining(plan, stage_counts)
    metric = getattr(st, "metric", None)
    caption = getattr(st, "caption", None)
    if callable(metric):
        metric("Actual so far", f"${actual:.2f}")
        metric("Projected total", f"${actual + remainder:.2f}")
        if callable(caption):
            caption("Based on model mix and current plan; updates live. ±20% uncertainty")
