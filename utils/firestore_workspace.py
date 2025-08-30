from __future__ import annotations

import hashlib
import re
import time
from typing import TYPE_CHECKING, Any

import streamlit as st

from utils.lazy_import import lazy

if TYPE_CHECKING:  # pragma: no cover - typing only
    from google.cloud import firestore  # type: ignore

_firestore = lazy("google.cloud.firestore")
_service_account = lazy("google.oauth2.service_account")

_COLLECTION = "rd_projects"  # single namespace!


def _client() -> firestore.Client:
    try:
        info = dict(st.secrets["gcp_service_account"])
        creds = _service_account.Credentials.from_service_account_info(info)
        return _firestore.Client(credentials=creds, project=info["project_id"])
    except Exception:
        return _firestore.Client()  # fallback to ADC


def _slugify(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"(^-|-$)", "", s)


class FirestoreWorkspace:
    """Symbolic shared memory for one project."""

    def __init__(self, project_id: str, name: str | None = None):
        self.doc = _client().collection(_COLLECTION).document(project_id)
        if not self.doc.get().exists:
            if not name:
                raise ValueError("Project name is required.")
            slug = _slugify(name)
            if slug != project_id:
                raise ValueError("Project ID must match slug of name.")
            self.doc.set(
                {
                    "name": name,
                    "slug": slug,
                    "updatedAt": _firestore.SERVER_TIMESTAMP,
                    "createdAt": _firestore.SERVER_TIMESTAMP,
                    "idea": "",
                    "tasks": [],  # [{id, role, task, status}]
                    "results": {},  # id -> result blob
                    "scores": {},  # id -> float
                    "history": [],
                    "cycle": 0,
                }
            )

    # ---------- helpers ----------
    def read(self) -> dict[str, Any]:
        return self.doc.get().to_dict()

    def patch(self, d: dict[str, Any]):  # generic update
        self.doc.update(d)

    def append(self, key: str, items: list):
        doc = self.read()
        arr = list(doc.get(key, []))
        arr.extend(items or [])
        self.patch({key: arr})

    # ---------- task queue ----------
    def enqueue(self, tasks: list[dict[str, str]]):
        self.doc.update({"tasks": _firestore.ArrayUnion(tasks)})

    def pop(self) -> dict[str, str] | None:
        data = self.read()
        if not data["tasks"]:
            return None
        nxt, q = data["tasks"][0], data["tasks"][1:]
        self.doc.update({"tasks": q})
        return nxt

    # ---------- results / logging ----------
    def save_result(self, tid: str, result: Any, score: float):
        self.doc.update({f"results.{tid}": result, f"scores.{tid}": score})

    def log(self, msg: str):
        self.doc.update({"history": _firestore.ArrayUnion([msg])})

    # ---------- utils ----------
    @staticmethod
    def new_id(role: str) -> str:
        return hashlib.sha1(f"{role}{time.time()}".encode()).hexdigest()[:10]
