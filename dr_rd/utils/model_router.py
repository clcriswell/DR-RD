from dr_rd.config.model_routing import DEFAULTS, CallHints


def pick_model(h: CallHints) -> dict:
    # plan
    if h.stage == "plan":
        model = DEFAULTS["PLANNER"]
        params = {"reasoning_effort": "minimal", "verbosity": "low"}
        if h.difficulty == "hard":
            model = "o4-mini"
            params["reasoning_effort"] = "medium"
        return {"model": model, "params": params}

    # exec (researchers/retrievers/agents)
    if h.stage == "exec":
        model = DEFAULTS["RESEARCHER"]
        params = {"reasoning_effort": "minimal", "verbosity": "low"}
        if h.difficulty == "hard":
            model = "gpt-5-mini"
        return {"model": model, "params": params}

    # eval
    if h.stage == "eval":
        return {
            "model": DEFAULTS["EVALUATOR"],
            "params": {"reasoning_effort": "minimal", "verbosity": "low"},
        }

    # brain loop
    if h.stage == "brain":
        model = DEFAULTS["BRAIN_MODE_LOOP"]
        params = {"reasoning_effort": "medium", "verbosity": "low"}
        if h.deep_reasoning:
            model = "o3"
            params["reasoning_effort"] = "high"
        return {"model": model, "params": params}

    # synth
    if h.stage == "synth":
        model = DEFAULTS["SYNTHESIZER"]
        params = {"reasoning_effort": "minimal", "verbosity": "medium"}
        if h.final_pass:
            model = DEFAULTS["FINAL_SYNTH"]
            params["reasoning_effort"] = "medium"
            params["verbosity"] = "high"
        return {"model": model, "params": params}

    return {
        "model": DEFAULTS["RESEARCHER"],
        "params": {"reasoning_effort": "minimal", "verbosity": "low"},
    }


def difficulty_from_signals(score: float, coverage: float) -> str:
    if score >= 0.82 and coverage >= 0.65:
        return "easy"
    if score < 0.72 or coverage < 0.45:
        return "hard"
    return "normal"
