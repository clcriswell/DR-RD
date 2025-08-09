from dr_rd.utils.token_meter import TokenMeter
from dr_rd.config.pricing import cost_usd
import streamlit as st

METER = TokenMeter()

ALLOWED_PARAMS = {
    "temperature",
    "response_format",
    "max_tokens",
    "top_p",
}


def log_usage(stage, model, pt, ct):
    if "usage_log" not in st.session_state:
        st.session_state["usage_log"] = []
    st.session_state["usage_log"].append({"stage": stage, "model": model, "pt": pt, "ct": ct})


def llm_call(client, model_id: str, stage: str, messages: list, **params):
    safe = {k: v for k, v in params.items() if k in ALLOWED_PARAMS}
    resp = client.chat.completions.create(model=model_id, messages=messages, **safe)
    usage_obj = resp.choices[0].usage if hasattr(resp.choices[0], "usage") else getattr(resp, "usage", None)
    if isinstance(usage_obj, dict):
        usage = {
            "prompt_tokens": usage_obj.get("prompt_tokens", 0),
            "completion_tokens": usage_obj.get("completion_tokens", 0),
            "total_tokens": usage_obj.get("total_tokens", 0),
        }
    else:
        usage = {
            "prompt_tokens": getattr(usage_obj, "prompt_tokens", 0),
            "completion_tokens": getattr(usage_obj, "completion_tokens", 0),
            "total_tokens": getattr(usage_obj, "total_tokens", 0),
        }
    try:
        METER.add_usage(model_id, stage, usage)
    except Exception:
        pass
    return resp
