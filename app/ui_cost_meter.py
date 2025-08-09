import streamlit as st
from dr_rd.config.model_routing import MODEL_PRICES
from dr_rd.config.mode_profiles import UI_PRESETS


def estimate_tokens_brief(brief_len_tokens: int, base_exec_tokens: int, help_prob: float = 0.3):
    plan_tokens = int(1.2 * brief_len_tokens)
    exec_tokens = int(base_exec_tokens * 1.35)        # slight expansion during exec
    eval_tokens = 800 * 3                              # heuristic evaluator overhead
    extra = help_prob * (int(0.7 * plan_tokens) + base_exec_tokens + eval_tokens)
    return plan_tokens + exec_tokens + eval_tokens + int(extra)


def _rough_tokens_from_text(txt: str) -> int:
    # ~4 chars per token heuristic
    if not txt:
        return 500
    return max(500, int(len(txt) / 4))


def render_estimator(mode: str, idea_text: str, price_per_1k: float = 0.005):
    st.subheader("Run Cost Estimate")
    preset = UI_PRESETS.get(mode, UI_PRESETS["balanced"])
    brief_tokens = _rough_tokens_from_text(idea_text)
    base_exec = preset["estimator"]["exec_tokens"]
    help_prob = preset["estimator"]["help_prob"]
    est = estimate_tokens_brief(brief_tokens, base_exec, help_prob=help_prob)
    st.metric("Estimated tokens", f"{est:,}")
    st.metric("Estimated $", f"${est/1000*price_per_1k:,.4f}")
    with st.expander("Model prices"):
        st.json(MODEL_PRICES)

