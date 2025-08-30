import streamlit as st

from utils.usage import Usage, thresholds


def render_live(usage: Usage, *, budget_limit_usd: float | None, token_limit: int | None):
    """Render live usage meters."""
    th = thresholds(usage, budget_limit_usd=budget_limit_usd, token_limit=token_limit)
    cost_col, tok_col = st.columns(2)

    if budget_limit_usd is not None:
        frac = th["budget_frac"] or 0.0
        cost_col.progress(min(frac, 1.0))
        cost_col.caption(f"$ {usage.cost_usd:.2f} / {budget_limit_usd}")
        if 0.8 <= frac < 1.0:
            cost_col.warning(f"Budget {frac:.0%}")
    else:
        cost_col.metric("Cost", f"$ {usage.cost_usd:.2f}")

    if token_limit is not None:
        frac = th["token_frac"] or 0.0
        tok_col.progress(min(frac, 1.0))
        tok_col.caption(f"{usage.total_tokens} / {token_limit} tokens")
        if 0.8 <= frac < 1.0:
            tok_col.warning(f"Tokens {frac:.0%}")
    else:
        tok_col.metric("Tokens", f"{usage.total_tokens}")

    return th


def render_summary(usage: Usage):
    """Render a compact usage summary."""
    col1, col2 = st.columns(2)
    col1.metric("Total cost", f"$ {usage.cost_usd:.2f}")
    col2.metric("Total tokens", f"{usage.total_tokens}")
