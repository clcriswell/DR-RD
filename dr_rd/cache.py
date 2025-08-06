"""Firestore-backed result cache for DR-RD."""
from __future__ import annotations

from typing import Optional

import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account

_client: Optional[firestore.Client] = None


def _get_client() -> Optional[firestore.Client]:
    """Return a Firestore client, creating it if needed.
    If the client cannot be created (e.g. credentials missing), ``None`` is returned.
    """
    global _client
    if _client is None:
        try:
            info = st.secrets["gcp_service_account"]
            credentials = service_account.Credentials.from_service_account_info(info)
            _client = firestore.Client(credentials=credentials)
        except Exception:
            try:
                _client = firestore.Client()
            except Exception:
                _client = None
    return _client


def get_result(hash: str) -> Optional[str]:
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
