"""Run page for the DR-RD Streamlit application."""

from app import main
from utils.telemetry import log_event


def run() -> None:
    """Launch the DR-RD Streamlit application."""
    log_event({"event": "nav_page_view", "page": "run"})
    main()


if __name__ == "__main__":
    run()
