import streamlit as st
from dr_rd.config.mode_profiles import UI_PRESETS
from dr_rd.config.pricing import cost_usd

PRIORS = {
    "plan": {"gpt-4o": 1500},
    "exec": {"gpt-4o-mini": 600},
    "synth": {"gpt-5": 4000},
}


def render_estimator(mode: str, idea_text: str, price_per_1k: float = 0.005):
    st.subheader("Run Cost Estimate")
    if mode == "test":
        st.info("**Test mode:** minimal-cost dry run to exercise all features.")
    preset = UI_PRESETS.get(mode, UI_PRESETS["balanced"]).get("estimator", {})
    tokens = preset.get("exec_tokens", 0)
    est_cost = tokens / 1000 * price_per_1k
    metric = getattr(st, "metric", None)
    if callable(metric):
        label = "Estimated Cost"
        if mode == "test":
            metric(label, f"${est_cost:.4f}", help="dev-only")
        else:
            metric(label, f"${est_cost:.2f}")

def render_cost_summary(mode: str, plan: dict | list | None):
    log = st.session_state.get("usage_log", [])
    actual = 0.0
    stage_counts = {}
    for entry in log:
        actual += cost_usd(entry["model"], entry["pt"], entry["ct"])
        stage_counts[entry["stage"]] = stage_counts.get(entry["stage"], 0) + 1

    preset = UI_PRESETS.get(mode, UI_PRESETS["balanced"])
    refinement_rounds = preset.get("refinement_rounds", 1)
    if isinstance(plan, dict):
        roles = len(plan.keys())
    elif isinstance(plan, list):
        roles = len({t.get("role") for t in plan})
    else:
        roles = 0
    expected_calls = {
        "plan": 1,
        "exec": roles * refinement_rounds,
        "synth": 1,
    }
    remainder = 0.0
    for stage, models in PRIORS.items():
        remaining = expected_calls.get(stage, 0) - stage_counts.get(stage, 0)
        if remaining <= 0:
            continue
        for model, toks in models.items():
            pt = toks // 2
            ct = toks - pt
            remainder += remaining * cost_usd(model, pt, ct)

    metric = getattr(st, "metric", None)
    caption = getattr(st, "caption", None)
    if callable(metric):
        metric("Actual so far", f"${actual:.2f}")
        metric("Projected total", f"${actual + remainder:.2f}")
        if callable(caption):
            caption("Based on model mix and current plan; updates live. ±20% uncertainty")
