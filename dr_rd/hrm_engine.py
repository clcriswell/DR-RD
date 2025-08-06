"""
hrm_engine.py  ── Hierarchical Reasoning core for DR RD
-------------------------------------------------------
Implements:
  • FirestoreWorkspace  – symbolic shared memory (per project)
  • HighLevelPlanner    – high level strategic thinker
  • LowLevelExecutor    – low level task performer
  • HRMLoop             – planner ↔ executor loop w/ global halting

Requires:
  • google-cloud-firestore (already in requirements.txt)
  • openai              (already in requirements.txt)
  • streamlit secrets:  OPENAI_API_KEY,  gcp_service_account (json)
"""

from __future__ import annotations
import hashlib, json, logging, os, time
from typing import Dict, List, Any, Optional

import openai
from google.cloud import firestore
from google.oauth2 import service_account
import streamlit as st

# ---------- CONFIG ----------
MAX_CYCLES          = 8   # upper bound on planner iterations
IMPROVE_THRESHOLD    = 0.01  # ↓ if using more granular scores
NO_PROGRESS_PATIENCE = 2   # cycles w/o improvement -> halt
openai.api_key       = os.getenv("OPENAI_API_KEY", st.secrets["OPENAI_API_KEY"])

# ---------- WORKSPACE ----------
class FirestoreWorkspace:
    """Symbolic shared memory living in a Firestore doc."""
    def __init__(self, project_id: str):
        self._client = self._init_client()
        self._doc    = self._client.collection("hrm_projects").document(project_id)
        self._ensure_seed()

    # --- Firestore init helper
    @staticmethod
    def _init_client() -> firestore.Client:
        try:
            creds_dict = st.secrets["gcp_service_account"]
            creds = service_account.Credentials.from_service_account_info(dict(creds_dict))
            return firestore.Client(credentials=creds)
        except Exception:
            return firestore.Client()  # hope default creds are present

    # --- Create document if missing
    def _ensure_seed(self):
        if not self._doc.get().exists:
            self._doc.set({
                "plan"      : [],
                "tasks"     : [],     # queue of {id, title, status, meta}
                "results"   : {},     # task_id -> result blob
                "metrics"   : {},     # task_id -> score/metric
                "cycle"     : 0,
                "history"   : [],
                "timestamp" : firestore.SERVER_TIMESTAMP,
            })

    # --- Convenience getters / setters
    def read(self) -> Dict[str, Any]:
        return self._doc.get().to_dict()

    def write(self, patch: Dict[str, Any]):
        self._doc.update(patch)

    # --- Helper update APIs -----------------
    def enqueue_tasks(self, tasks: List[Dict[str, Any]]):
        """Append new tasks to queue."""
        self._doc.update({"tasks": firestore.ArrayUnion(tasks)})

    def pop_next_task(self) -> Optional[Dict[str, Any]]:
        snap = self._doc.get()
        data = snap.to_dict()
        queue = data["tasks"]
        if not queue:
            return None
        task = queue[0]
        remainder = queue[1:]
        self._doc.update({"tasks": remainder})
        return task

    def save_result(self, task_id: str, result: Dict[str, Any], score: float):
        self._doc.update({
            f"results.{task_id}": result,
            f"metrics.{task_id}": score,
        })

    def log_history(self, entry: str):
        self._doc.update({"history": firestore.ArrayUnion([entry])})

# ---------- HIGH LEVEL PLANNER ----------
class HighLevelPlanner:
    """Uses GPT to inspect workspace + craft / revise task list."""
    SYSTEM_PROMPT = (
        "You are the Senior Architect for an R&D project. "
        "Given the current project state below, output JSON with two keys:\n"
        "  new_tasks: [ {title: str, description: str} ... ]  # tasks to add\n"
        "  important_notes: str  # one sentence rationale\n"
        "Focus on high level needs; do NOT propose solutions."
    )

    def __init__(self, workspace: FirestoreWorkspace):
        self.ws = workspace

    def step(self) -> int:
        state = self.ws.read()
        content = json.dumps(state, indent=2)[:8000]  # avoid token blow up
        messages = [
            {"role":"system", "content": self.SYSTEM_PROMPT},
            {"role":"user",   "content": content},
        ]
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            temperature=0.3,
            messages=messages
        )
        assistant_msg = resp.choices[0].message.content.strip()
        try:
            data = json.loads(assistant_msg)
            tasks = data.get("new_tasks", [])
        except Exception:
            tasks = []

        # Stamp tasks with IDs and enqueue
        stamped = []
        for t in tasks:
            tid = hashlib.sha1(f"{t['title']}{time.time()}".encode()).hexdigest()[:10]
            stamped.append({"id": tid, "title": t["title"], "status": "todo", "meta": t.get("description","")})
        if stamped:
            self.ws.enqueue_tasks(stamped)
            self.ws.log_history(f"Planner added {len(stamped)} tasks.")

        return len(stamped)   # how many tasks added

# ---------- LOW LEVEL EXECUTOR ----------
class LowLevelExecutor:
    """Grabs one task, performs concrete work, scores it, writes result."""
    SYSTEM_TPL = (
        "You are a domain expert executing the task below.\n"
        "Return a JSON with 'result' (object) and 'score' (float 0 1, 1=perfect).\n"
        "### TASK ###\n{task}\n\n"
        "### CONTEXT ###\n{context}\n"
    )

    def __init__(self, workspace: FirestoreWorkspace):
        self.ws = workspace

    def step(self) -> float:
        task = self.ws.pop_next_task()
        if not task:
            return 0.0  # nothing to do; signals possible halting
        context = self.ws.read()
        prompt = self.SYSTEM_TPL.format(task=json.dumps(task,indent=2),
                                        context=json.dumps(context["plan"])[:2000])
        messages = [{"role":"system", "content": prompt}]
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            temperature=0.4,
            messages=messages
        )
        assistant_msg = resp.choices[0].message.content.strip()
        try:
            data = json.loads(assistant_msg)
            result, score = data.get("result", {}), float(data.get("score", 0.0))
        except Exception:
            result, score = assistant_msg, 0.0

        self.ws.save_result(task_id=task["id"], result=result, score=score)
        self.ws.log_history(f"Executor finished {task['title']} score={score:.2f}")
        return score

# ---------- HRM LOOP & GLOBAL HALTING ----------
class HRMLoop:
    """Run Planner ↔ Executor until goals met or progress stalls."""
    def __init__(self, project_id: str):
        self.ws   = FirestoreWorkspace(project_id)
        self.plan = HighLevelPlanner(self.ws)
        self.exec = LowLevelExecutor(self.ws)

    def run(self):
        no_progress = 0
        last_best   = 0.0
        for cycle in range(MAX_CYCLES):
            self.ws.write({"cycle": cycle})
            added = self.plan.step()   # high level update
            score = self.exec.step()   # low level work
            best  = max(last_best, score)
            improvement = best - last_best

            # halting conditions
            if not added and improvement < IMPROVE_THRESHOLD:
                no_progress += 1
            else:
                no_progress = 0
            last_best = best
            if no_progress >= NO_PROGRESS_PATIENCE:
                self.ws.log_history("🛑 Halting: no progress")
                break
        self.ws.log_history("✅ HRM Loop complete")
