"""Logging configuration for the Streamlit app.

This module exposes :func:`init_gcp_logging` which attempts to initialize
Google Cloud Logging based on credentials provided via configuration. If the
credentials are missing or invalid, the application will continue to run with
standard Python logging instead of crashing.
"""

import json
import logging

from dr_rd.config.env import get_env

_GCP_LOGGED = False


def init_gcp_logging() -> bool:
    """Initialise Google Cloud Logging if credentials are available.

    Returns ``True`` if Cloud Logging was successfully initialised, otherwise
    ``False``. Any exception raised during initialisation is caught so the app
    can operate without GCP logging.
    """

    global _GCP_LOGGED
    if _GCP_LOGGED:
        return True

    logger = logging.getLogger()
    if any(
        getattr(h, "__class__", None).__name__.lower().startswith("gcl") for h in logger.handlers
    ):
        _GCP_LOGGED = True
        return True

    try:
        from google.cloud import logging as gcp_logging
        from google.oauth2 import service_account

        creds_raw = get_env("GCP_SERVICE_ACCOUNT")
        if not creds_raw:
            raise KeyError("missing gcp_service_account secret")
        creds_info = json.loads(creds_raw)
        if not creds_info.get("private_key"):
            raise KeyError("missing private_key in gcp_service_account secret")

        credentials = service_account.Credentials.from_service_account_info(creds_info)
        client = gcp_logging.Client(credentials=credentials)
        client.setup_logging()
        logging.info("✅ Google Cloud Logging initialized")
        _GCP_LOGGED = True
        return True
    except Exception as exc:  # pragma: no cover - best-effort logging
        logging.warning("⚠️ Google Cloud Logging disabled: %s", exc)
        _GCP_LOGGED = True
        return False


__all__ = ["init_gcp_logging"]
