"""Firestore-backed result cache for DR-RD."""
from __future__ import annotations

from typing import Optional

from google.cloud import firestore
from google.oauth2 import service_account
import streamlit as st

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


# --- FirestoreWorkspace: symbolic shared memory for tasks/results ---
class FirestoreWorkspace:
    def __init__(self, project_id: str):
        self._client = self._init_client()
        self._doc = self._client.collection("dr_rd_projects").document(project_id)
        if not self._doc.get().exists:
            self._doc.set({
                "tasks": [],         # list of {role, task, id}
                "results": {},       # id -> result
                "scores": {},        # id -> score
                "history": [],       # text logs
                "cycle": 0
            })

    @staticmethod
    def _init_client() -> firestore.Client:
        try:
            info = dict(st.secrets["gcp_service_account"])
            creds = service_account.Credentials.from_service_account_info(info)
            return firestore.Client(credentials=creds, project=info["project_id"])
        except Exception:
            return firestore.Client()

    def read(self) -> dict:
        return self._doc.get().to_dict()

    def write(self, patch: dict):
        self._doc.update(patch)

    def enqueue_tasks(self, tasks: list[dict]):
        self._doc.update({"tasks": firestore.ArrayUnion(tasks)})

    def get_next_task(self) -> dict | None:
        data = self.read()
        queue = data["tasks"]
        if not queue:
            return None
        task = queue.pop(0)
        self._doc.update({"tasks": queue})
        return task

    def save_result(self, task_id: str, result: any, score: float):
        self._doc.update({
            f"results.{task_id}": result,
            f"scores.{task_id}": score
        })

    def log(self, msg: str):
        self._doc.update({"history": firestore.ArrayUnion([msg])})

    def bump_cycle(self, n: int):
        self._doc.update({"cycle": n})
