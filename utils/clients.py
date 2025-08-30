from __future__ import annotations

from .cache import cached_resource
from .lazy_import import local_import


@cached_resource()
def get_firestore_client():
    """Return a Firestore client if libraries and credentials are available."""
    try:
        firestore = local_import("google.cloud.firestore")
        return firestore.Client()
    except Exception:
        return None


@cached_resource()
def get_cloud_logging_client():
    """Return a Cloud Logging client if available."""
    try:
        cloud_logging = local_import("google.cloud.logging")
        return cloud_logging.Client()
    except Exception:
        return None
