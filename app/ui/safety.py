import streamlit as st


def badge(result, *, where: str):
    if not result.findings:
        return
    sev = max((f.severity for f in result.findings), default="low")
    label = f"Safety: {sev.upper()} ({len(result.findings)})"
    st.caption(label)


def confirm_to_proceed(result, *, action_label="Proceed"):
    import streamlit as st  # local import per instructions

    if not result.findings:
        return True

    @st.dialog("Safety review")
    def _dlg():
        st.write("Potential risks detected.")
        for f in result.findings[:10]:
            st.write(f"- **{f.category}** — {f.message}")
        st.checkbox("I understand the risk", key="ack_risk")
        if st.session_state.get("ack_risk"):
            st.button(action_label, key="proceed_btn")

    _dlg()
    return st.session_state.get("ack_risk", False)


__all__ = ["badge", "confirm_to_proceed"]
