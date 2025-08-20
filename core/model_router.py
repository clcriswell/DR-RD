from config.model_routing import DEFAULTS, CallHints
import streamlit as st


def pick_model(h: CallHints) -> dict:
    if h.stage == "plan":
        sel = {"model": DEFAULTS["PLANNER"], "repair_model": "gpt-5", "params": {}}
        if h.difficulty == "hard":
            sel["model"] = "gpt-5"
    elif h.stage == "exec":
        sel = {"model": DEFAULTS["RESEARCHER"], "params": {}}
        if h.difficulty == "hard":
            sel["model"] = "gpt-5"
    elif h.stage == "eval":
        sel = {"model": DEFAULTS["EVALUATOR"], "params": {}}
    elif h.stage == "brain":
        model = DEFAULTS["BRAIN_MODE_LOOP"]
        if h.deep_reasoning:
            model = "gpt-5"
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
            sel["model"] = flags.get("MODEL_EXEC", "gpt-5")
        params = sel.get("params", {})
        params["temperature"] = min(0.3, params.get("temperature", 0.3))
        sel["params"] = params

    if "MODE_CFG" in st.session_state and "models" in st.session_state["MODE_CFG"]:
        stage_map = st.session_state["MODE_CFG"].get("models", {})
        if h.stage == "plan":
            sel["model"] = stage_map.get("plan", sel["model"])
        elif h.stage == "exec":
            sel["model"] = stage_map.get("exec", sel["model"])
        elif h.stage == "synth":
            sel["model"] = stage_map.get("synth", sel["model"])
    return sel


def difficulty_from_signals(score: float, coverage: float) -> str:
    if score >= 0.82 and coverage >= 0.65:
        return "easy"
    if score < 0.72 or coverage < 0.45:
        return "hard"
    return "normal"
