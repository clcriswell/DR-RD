from dr_rd.utils.token_meter import TokenMeter

METER = TokenMeter()


ALLOWED_PARAMS = {
    "reasoning_effort",
    "verbosity",
    "temperature",
    "response_format",
    "max_tokens",
    "top_p",
}


def llm_call(client, model_id: str, stage: str, messages: list, **params):
    safe = {k: v for k, v in params.items() if k in ALLOWED_PARAMS}
    resp = client.chat.completions.create(model=model_id, messages=messages, **safe)
    usage = getattr(resp, "usage", None) or {}
    try:
        METER.add_usage(
            model_id,
            stage,
            {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
        )
    except Exception:
        pass
    return resp
