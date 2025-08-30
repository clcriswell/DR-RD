from __future__ import annotations

from .cache import cached_resource


@cached_resource()
def get_firestore_client():
    """Return a Firestore client if libraries and credentials are available."""
    try:
        from google.cloud import firestore  # type: ignore

        return firestore.Client()
    except Exception:
        return None


@cached_resource()
def get_cloud_logging_client():
    """Return a Cloud Logging client if available."""
    try:
        from google.cloud import logging as cloud_logging  # type: ignore

        return cloud_logging.Client()
    except Exception:
        return None
