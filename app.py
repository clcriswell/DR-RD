"""Streamlit entry point for the DR-RD application.

This file exists so that ``streamlit run app.py`` finds the application
module. The bulk of the app lives in the ``app`` package; this script
imports the package and executes ``main()`` to build the interface.
"""

from app import main


if __name__ == "__main__":
    main()
