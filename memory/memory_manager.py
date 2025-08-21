from __future__ import annotations
from typing import Any, Optional, Dict
import time
import json
import os
import logging
import uuid
import re
from difflib import SequenceMatcher

from utils.config import load_config
from filelock import FileLock


def _slugify(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s[:64] or "project"


class MemoryManager:
    """Session-scoped in-process memory with TTL support and project persistence."""

    def __init__(self, file_path: str = "memory/project_memory.json", ttl_default: Optional[int] = None):
        self.file_path = file_path
        self._lock = FileLock(f"{self.file_path}.lock")
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        try:
            with self._lock, open(self.file_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.data = []
        if not isinstance(self.data, list):
            self.data = []
        for entry in self.data:
            entry.setdefault("constraints", "")
            entry.setdefault("risk_posture", "Medium")

        cfg = load_config()
        ttl_cfg = cfg.get("memory", {}).get("ttl_seconds", 86400)
        self.ttl_default = ttl_default if ttl_default is not None else ttl_cfg
        self.store: Dict[str, Dict[str, tuple[Any, Optional[float]]]] = {}

    def set(self, key: str, value: Any, *, session_id: str, ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.ttl_default
        expires = time.time() + ttl if ttl else None
        self.store.setdefault(session_id, {})[key] = (value, expires)

    def get(self, key: str, *, session_id: str) -> Optional[Any]:
        sess = self.store.get(session_id, {})
        val = sess.get(key)
        if not val:
            return None
        value, expires = val
        if expires is not None and expires < time.time():
            del sess[key]
            if not sess:
                self.store.pop(session_id, None)
            return None
        return value

    def delete(self, key: str, *, session_id: str) -> None:
        sess = self.store.get(session_id)
        if sess and key in sess:
            del sess[key]
            if not sess:
                self.store.pop(session_id, None)

    def clear_session(self, session_id: str) -> None:
        self.store.pop(session_id, None)

    def prune(self) -> int:
        now = time.time()
        removed = 0
        for session_id in list(self.store.keys()):
            sess = self.store[session_id]
            for key in list(sess.keys()):
                _, exp = sess[key]
                if exp is not None and exp < now:
                    del sess[key]
                    removed += 1
            if not sess:
                del self.store[session_id]
        return removed

    # Legacy project persistence helpers
    def store_project(
        self,
        name,
        idea,
        plan,
        results,
        proposal,
        images=None,
        *,
        constraints: str | None = None,
        risk_posture: str | None = None,
    ):
        entry = {
            "name": name,
            "idea": idea,
            "plan": plan,
            "results": results,
            "proposal": proposal,
            "images": images or [],
            "constraints": constraints or "",
            "risk_posture": risk_posture or "Medium",
        }
        try:  # pragma: no cover - optional Firestore
            if name:
                import streamlit as st
                from google.cloud import firestore
                from google.oauth2 import service_account

                if "gcp_service_account" in st.secrets:
                    creds = service_account.Credentials.from_service_account_info(
                        st.secrets["gcp_service_account"]
                    )
                    db = firestore.Client(credentials=creds, project=creds.project_id)
                    doc_id = _slugify(name)
                    db.collection("rd_projects").document(doc_id).set(entry)
                else:
                    logging.info(
                        "Firestore save skipped: missing gcp_service_account secret"
                    )
            else:
                logging.info("Firestore save skipped: project name is required")
        except Exception as e:  # pylint: disable=broad-except
            logging.info(
                f"Firestore save skipped: invalid gcp_service_account secret ({e})"
            )

        self.data.append(entry)
        with self._lock, open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def find_similar_ideas(self, idea, top_n=3):
        idea_lower = idea.lower()
        similarities = []
        for entry in self.data:
            past_idea = entry.get("idea", "")
            if not past_idea:
                continue
            ratio = SequenceMatcher(None, idea_lower, past_idea.lower()).ratio()
            if ratio > 0.3:
                similarities.append((ratio, past_idea))
        similarities.sort(reverse=True, key=lambda x: x[0])
        return [idea for _, idea in similarities[:top_n]]

    def get_project_summaries(self, similar_ideas_list):
        summaries = []
        for idea_text in similar_ideas_list:
            for entry in self.data:
                if entry.get("idea") == idea_text:
                    proposal = entry.get("proposal", "")
                    summary_text = ""
                    if proposal:
                        text_lower = proposal.lower()
                        idx = text_lower.find("summary")
                        if idx != -1:
                            next_heading_idx = text_lower.find("##", idx + 1)
                            if next_heading_idx != -1:
                                summary_text = proposal[idx:next_heading_idx].strip()
                            else:
                                summary_text = proposal[idx: idx + 200].strip()
                        else:
                            summary_text = proposal[:200].strip()
                        if len(proposal) > 200:
                            summary_text += "..."
                    else:
                        summary_text = "(No proposal available)"
                    summaries.append(f"**Idea:** {idea_text}\n**Summary:** {summary_text}")
                    break
        return "\n\n".join(summaries)


    # --- PoC helpers ---
    def attach_poc(self, project_id: str, test_plan: dict, poc_report: dict) -> None:
        """Attach PoC artefacts to the project record."""
        entry = next((e for e in self.data if e.get("name") == project_id), None)
        if entry is None:
            entry = {"name": project_id}
            self.data.append(entry)
        entry["test_plan"] = test_plan
        entry["poc_report"] = poc_report
        with self._lock, open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)
