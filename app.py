"""Streamlit entry point for the DR-RD application.

This file exists so that ``streamlit run app.py`` finds the application
module. The bulk of the app lives in the ``app`` package; this script
provides a small router that can either launch the main application or
invoke additional tools such as the geometry previewer.
"""

from app import main
from agents.geometry_tool import show_geometry
import streamlit as st


def tool_router():
    """Route to the main app or a registered tool."""
    tool = st.sidebar.selectbox("Action", ["app", "geometry"], index=0)

    if tool == "geometry":
        with st.form("geometry_form"):
            width = st.number_input("Width", value=1.0)
            height = st.number_input("Height", value=2.0)
            depth = st.number_input("Depth", value=3.0)
            submitted = st.form_submit_button("Preview")
        if submitted:
            spec = {
                "type": "cube",
                "params": {"width": width, "height": height, "depth": depth},
            }
            show_geometry(spec)
    else:
        main()


if __name__ == "__main__":
    tool_router()
