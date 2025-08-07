"""Streamlit entry point for the DR-RD application.

This file exists so that ``streamlit run app.py`` finds the application
module. The bulk of the app lives in the ``app`` package; this script
provides a small router that can either launch the main application or
invoke additional tools.
"""

from app import main


def tool_router():
    """Route directly to the main app."""
    main()


if __name__ == "__main__":
    tool_router()
