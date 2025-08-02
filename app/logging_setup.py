"""Logging configuration for the Streamlit app.

This module attempts to initialize Google Cloud Logging based on
credentials provided via ``st.secrets``. If the credentials are missing or
invalid, the application will continue to run with standard Python logging
instead of crashing at import time.
"""

import logging
import streamlit as st


def init_gcp_logging() -> bool:
    """Initialise Google Cloud Logging if credentials are available.

    Returns ``True`` if Cloud Logging was successfully initialised, otherwise
    ``False``. Any exception raised during initialisation is caught so the app
    can operate without GCP logging.
    """

    try:
        from google.cloud import logging as gcp_logging
        from google.oauth2 import service_account

        # Extract service account credentials from Streamlit secrets.
        creds_info = dict(st.secrets["gcp_service_account"])
        if not creds_info.get("private_key"):
            raise KeyError("missing private_key in gcp_service_account secret")

        credentials = service_account.Credentials.from_service_account_info(
            creds_info
        )
        client = gcp_logging.Client(credentials=credentials)
        client.setup_logging()
        logging.info("✅ Google Cloud Logging initialized")
        return True
    except Exception as exc:  # pragma: no cover - best-effort logging
        logging.warning("⚠️ Google Cloud Logging disabled: %s", exc)
        return False


# Run on import but ignore failures
init_gcp_logging()

