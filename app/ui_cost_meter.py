import streamlit as st
from dr_rd.config.model_routing import MODEL_PRICES


def estimate_tokens_brief(
    brief_len_tokens: int,
    base_exec_tokens: int,
    agent_hrm_factor: float = 1.35,
    eval_calls: int = 3,
    help_prob: float = 0.3,
):
    plan_tokens = int(1.2 * brief_len_tokens)
    exec_tokens = int(base_exec_tokens * agent_hrm_factor)
    eval_tokens = 800 * eval_calls
    extra = help_prob * (int(0.7 * plan_tokens) + base_exec_tokens + eval_tokens)
    return plan_tokens + exec_tokens + eval_tokens + int(extra)


def render_estimator(
    default_brief_tokens: int = 2000,
    default_exec_tokens: int = 80000,
    price_per_1k: float = 0.005,
    help_prob: float = 0.3,
):
    st.subheader("Run Cost Estimate")
    brief = st.number_input("Brief size (tokens)", value=default_brief_tokens, step=500)
    exec_base = st.number_input(
        "Base exec tokens (classic)", value=default_exec_tokens, step=5000
    )
    p = st.slider("Chance of help step", 0.0, 1.0, help_prob, 0.05)
    est = estimate_tokens_brief(brief, exec_base, help_prob=p)
    st.metric("Estimated tokens", f"{est:,}")
    st.metric("Estimated $", f"${est/1000*price_per_1k:,.4f}")
    with st.expander("Model prices"):
        st.json(MODEL_PRICES)
