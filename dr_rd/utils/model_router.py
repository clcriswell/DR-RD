from dr_rd.config.model_routing import DEFAULTS, CallHints


def pick_model(h: CallHints) -> dict:
    # plan
    if h.stage == "plan":
        model = DEFAULTS["PLANNER"]
        if h.difficulty == "hard":
            model = "o4-mini"
        return {"model": model, "params": {}}

    # exec (researchers/retrievers/agents)
    if h.stage == "exec":
        model = DEFAULTS["RESEARCHER"]
        if h.difficulty == "hard":
            model = "gpt-5-mini"
        return {"model": model, "params": {}}

    # eval
    if h.stage == "eval":
        return {"model": DEFAULTS["EVALUATOR"], "params": {}}

    # brain loop
    if h.stage == "brain":
        model = DEFAULTS["BRAIN_MODE_LOOP"]
        if h.deep_reasoning:
            model = "o3"
        return {"model": model, "params": {}}

    # synth
    if h.stage == "synth":
        model = DEFAULTS["SYNTHESIZER"]
        if h.final_pass:
            model = DEFAULTS["FINAL_SYNTH"]
        return {"model": model, "params": {}}

    return {"model": DEFAULTS["RESEARCHER"], "params": {}}


def difficulty_from_signals(score: float, coverage: float) -> str:
    if score >= 0.82 and coverage >= 0.65:
        return "easy"
    if score < 0.72 or coverage < 0.45:
        return "hard"
    return "normal"
