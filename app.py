"""Streamlit entry point for the DR-RD application.

This file exists so that ``streamlit run app.py`` finds the application
module. The bulk of the app lives in the ``app`` package; this script
provides a small router that can either launch the main application or
invoke additional tools.
"""

from app import main
import streamlit as st


def tool_router():
    """Route to the main app or a registered tool."""
    tool = st.sidebar.selectbox("Action", ["app", "HRM R&D"], index=0)

    if tool == "HRM R&D":
        st.title("🧠 Hierarchical R&D Runner")
        idea = st.text_area("Project idea")
        pid = st.text_input("Project ID", value="demo-project")
        if st.button("Run HRM Loop"):
            from dr_rd.hrm_engine import HRMLoop
            with st.spinner("Working…"):
                HRMLoop(pid, idea).run()
            st.success("Done! view history in Firestore 📑")
    else:
        main()


if __name__ == "__main__":
    tool_router()
