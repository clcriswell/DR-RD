"""Run page for the DR-RD Streamlit application."""

from dr_rd.config import env as _env  # noqa: F401
from app import main


if __name__ == "__main__":
    main()
