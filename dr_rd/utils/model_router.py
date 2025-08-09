from dr_rd.config.model_routing import DEFAULTS, CallHints
import streamlit as st


def pick_model(h: CallHints) -> dict:
    if h.stage == "plan":
        sel = {"model": DEFAULTS["PLANNER"], "params": {}}
        if h.difficulty == "hard":
            sel["model"] = "o4-mini"
    elif h.stage == "exec":
        sel = {"model": DEFAULTS["RESEARCHER"], "params": {}}
        if h.difficulty == "hard":
            sel["model"] = "gpt-5-mini"
    elif h.stage == "eval":
        sel = {"model": DEFAULTS["EVALUATOR"], "params": {}}
    elif h.stage == "brain":
        model = DEFAULTS["BRAIN_MODE_LOOP"]
        if h.deep_reasoning:
            model = "o3"
        sel = {"model": model, "params": {}}
    elif h.stage == "synth":
        model = DEFAULTS["SYNTHESIZER"]
        if h.final_pass:
            model = DEFAULTS["FINAL_SYNTH"]
        sel = {"model": model, "params": {}}
    else:
        sel = {"model": DEFAULTS["RESEARCHER"], "params": {}}

    flags = st.session_state.get("final_flags", {}) if "st" in globals() else {}
    if flags.get("TEST_MODE"):
        override = {
            "plan": flags.get("MODEL_PLANNER"),
            "exec": flags.get("MODEL_EXEC"),
            "synth": flags.get("MODEL_SYNTH"),
        }.get(h.stage)
        if override:
            sel["model"] = override
        else:
            sel["model"] = flags.get("MODEL_EXEC", "gpt-4o-mini")
        params = sel.get("params", {})
        params["max_tokens"] = min(800, params.get("max_tokens", 800))
        params["temperature"] = min(0.3, params.get("temperature", 0.3))
        sel["params"] = params
    return sel


def difficulty_from_signals(score: float, coverage: float) -> str:
    if score >= 0.82 and coverage >= 0.65:
        return "easy"
    if score < 0.72 or coverage < 0.45:
        return "hard"
    return "normal"
