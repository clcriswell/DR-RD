"""Firestore-backed result cache for DR-RD."""

from __future__ import annotations

from typing import TYPE_CHECKING

import json

from dr_rd.config.env import get_env
from utils.lazy_import import lazy

if TYPE_CHECKING:  # pragma: no cover
    from google.cloud import firestore  # type: ignore

_firestore = lazy("google.cloud.firestore")
_service_account = lazy("google.oauth2.service_account")

_client: firestore.Client | None = None


def _get_client() -> firestore.Client | None:
    """Return a Firestore client, creating it if needed.
    If the client cannot be created (e.g. credentials missing), ``None`` is returned.
    """
    global _client
    if _client is None:
        try:
            info_raw = get_env("GCP_SERVICE_ACCOUNT")
            if info_raw:
                info = json.loads(info_raw)
                credentials = _service_account.Credentials.from_service_account_info(info)
                _client = _firestore.Client(credentials=credentials)
            else:
                _client = _firestore.Client()
        except Exception:
            try:
                _client = _firestore.Client()
            except Exception:
                _client = None
    return _client


def get_result(hash: str) -> str | None:
    """Retrieve cached result for ``hash`` or ``None`` if not found."""
    client = _get_client()
    if client is None:
        return None
    try:
        doc = client.collection("task_cache").document(hash).get()
        if doc.exists:
            data = doc.to_dict() or {}
            return data.get("content")
    except Exception:
        return None
    return None


def save_result(hash: str, content: str) -> None:
    """Store ``content`` for ``hash``. Best effort – failures are ignored."""
    client = _get_client()
    if client is None:
        return
    try:
        client.collection("task_cache").document(hash).set({"content": content})
    except Exception:
        pass


# replaced by unified utils.firestore_workspace
