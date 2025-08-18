from __future__ import annotations

from pathlib import Path
import yaml
import streamlit as st

from app.config_loader import load_mode
from dr_rd.utils.llm_client import set_budget_manager
from core.orchestrator import run_pipeline


def _available_modes() -> list[str]:
    # Read from the same config used by load_mode()
    try:
        from app.config_loader import CONFIG_DIR  # type: ignore
        with open(Path(CONFIG_DIR) / "modes.yaml", "r") as fh:
            d = yaml.safe_load(fh) or {}
        # Preserve a stable ordering
        order = ["test", "fast", "balanced", "deep"]
        return [m for m in order if m in d] or list(d.keys())
    except Exception:
        return ["test", "balanced", "deep"]

def render_lite() -> None:
    st.header("DR‑RD Lite")

    idea = st.text_area("Project Idea", key="lite_idea")
    modes = _available_modes()
    idx = max(0, modes.index("balanced") if "balanced" in modes else 0)
    mode = st.selectbox("Mode", modes, index=idx, key="lite_mode")

    if st.button("Run", key="lite_run"):
        if not idea:
            st.warning("Please provide an idea")
            st.stop()

        # Hard spend cap via BudgetManager
        mode_cfg, budget = load_mode(mode)
        set_budget_manager(budget)

        # Prevent accidental duplicate execution on repeated clicks
        run_key = (mode, (idea or "").strip())
        if st.session_state.get("LITE_LAST_RUN") == run_key:
            st.stop()
        st.session_state["LITE_LAST_RUN"] = run_key

        final, _, trace = run_pipeline(idea, mode=mode)

        st.subheader("Synthesis")
        st.write(final)

        with st.expander("Agent Trace", expanded=False):
            for item in (trace or []):
                agent = item.get("agent", "?")
                tokens = item.get("tokens", "?")
                finding = item.get("finding", "")
                st.write(f"{agent} ({tokens} tokens): {finding}")
