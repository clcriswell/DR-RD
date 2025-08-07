"""Streamlit entry point for the DR-RD application.

This file exists so that ``streamlit run app.py`` finds the application
module. The bulk of the app lives in the ``app`` package; this script
provides a small router that can either launch the main application or
invoke additional tools.
"""

from app import main, generate_pdf
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
            log_box = st.empty()
            logs = []

            def cb(msg: str) -> None:
                logs.append(msg)
                log_box.write("\n".join(logs))

            with st.spinner("Working…"):
                state, report = HRMLoop(pid, idea).run(log_callback=cb)

            st.success("Done! See results below and history in Firestore 📑")
            if report:
                st.subheader("Final Report")
                st.markdown(report)
                pdf_bytes = generate_pdf(report)
                st.download_button(
                    label="📄 Download Final Report as PDF",
                    data=pdf_bytes,
                    file_name="R&D_Report.pdf",
                    mime="application/pdf",
                )
            st.subheader("Results")
            st.json(state.get("results", {}))
    else:
        main()


if __name__ == "__main__":
    tool_router()
