from __future__ import annotations
import hashlib, time
from typing import Any, Dict, List, Optional

from google.cloud import firestore
from google.oauth2 import service_account
import streamlit as st

_COLLECTION = "dr_rd_projects"          # single namespace!

def _client() -> firestore.Client:
    try:
        info = dict(st.secrets["gcp_service_account"])
        creds = service_account.Credentials.from_service_account_info(info)
        return firestore.Client(credentials=creds, project=info["project_id"])
    except Exception:
        return firestore.Client()            # fallback to ADC

class FirestoreWorkspace:
    """Symbolic shared memory for one project."""
    def __init__(self, project_id: str):
        self.doc = _client().collection(_COLLECTION).document(project_id)
        if not self.doc.get().exists:
            self.doc.set({
                "idea": "",
                "tasks": [],          # [{id, role, task, status}]
                "results": {},        # id -> result blob
                "scores": {},         # id -> float
                "history": [],
                "cycle": 0,
            })

    # ---------- helpers ----------
    def read(self) -> Dict[str, Any]:
        return self.doc.get().to_dict()

    def patch(self, d: Dict[str, Any]):              # generic update
        self.doc.update(d)

    # ---------- task queue ----------
    def enqueue(self, tasks: List[Dict[str, str]]):
        self.doc.update({"tasks": firestore.ArrayUnion(tasks)})

    def pop(self) -> Optional[Dict[str, str]]:
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
        self.doc.update({"history": firestore.ArrayUnion([msg])})

    # ---------- utils ----------
    @staticmethod
    def new_id(role: str) -> str:
        return hashlib.sha1(f"{role}{time.time()}".encode()).hexdigest()[:10]
