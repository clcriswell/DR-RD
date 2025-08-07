"""HRM engine using FirestoreWorkspace and specialized agents."""
from __future__ import annotations

from typing import Tuple, Callable, Optional, Dict, Any, List

import time

from config import MAX_CONCURRENCY
from config.feature_flags import PARALLEL_EXEC_ENABLED
from dr_rd.engine.executor import run_tasks

from dr_rd.utils.firestore_workspace import FirestoreWorkspace as WS
from agents import initialize_agents
from dr_rd.extensions.registry import (
    EvaluatorRegistry,
    PlannerStrategyRegistry,
    SimulatorRegistry,
    MetaAgentRegistry,
)


class HRMLoop:
    def __init__(self, project_id: str, idea: str):
        self.ws = WS(project_id)
        self.idea = idea
        self.agents = initialize_agents()
        self.plan = self.agents["Planner"]
        self.synth = self.agents["Synthesizer"]
        # store idea once
        if not self.ws.read().get("idea"):
            self.ws.patch({"idea": idea})

    # ---------- execution helpers ----------
    def _execute(self, task: dict) -> Tuple[dict, float]:
        agent = self.agents.get(task["role"])
        if not agent:
            raise ValueError(f"No agent for role {task['role']}")
        result = agent.run(self.idea, task["task"])
        return result, 1.0

    # ---------- main loop ----------
    def run(
        self,
        max_cycles: int = 5,
        log_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[Dict[str, Any], str]:
        """Run the hierarchical R&D loop.

        Parameters
        ----------
        max_cycles:
            Maximum planning/execution cycles to perform.
        log_callback:
            Optional function invoked with each log message. This allows
            callers (e.g., Streamlit apps) to display progress in real time.

        Returns
        -------
        state, report:
            Final Firestore workspace state and the synthesized report
            produced by the ``Synthesizer`` agent.
        """

        def _log(msg: str) -> None:
            """Log to Firestore and the optional callback."""
            self.ws.log(msg)
            if log_callback:
                log_callback(msg)

        # Seed initial tasks
        if not self.ws.read()["tasks"]:
            seed = self.plan.run(self.idea, "Develop a plan")
            first = [
                {
                    "id": WS.new_id(role),
                    "role": role,
                    "task": t,
                    "status": "todo",
                    "priority": 0,
                    "created_at": time.time(),
                    "depends_on": [],
                }
                for role, t in seed.items()
            ]
            self.ws.enqueue(first)
            _log(f"🌱 seeded {len(first)} tasks from PlannerAgent")

        for cycle in range(max_cycles):
            self.ws.patch({"cycle": cycle})
            if PARALLEL_EXEC_ENABLED:
                batch: List[dict] = []
                while True:
                    t = self.ws.pop()
                    if not t:
                        break
                    batch.append(t)
                executed, pending = run_tasks(batch, MAX_CONCURRENCY, self, _log)
                if pending:
                    self.ws.enqueue(pending)
            else:
                pending_seq: List[dict] = []
                while True:
                    t = self.ws.pop()
                    if not t:
                        break
                    if any(
                        dep not in self.ws.read().get("results", {})
                        for dep in t.get("depends_on", [])
                    ):
                        pending_seq.append(t)
                        continue
                    _log(f"▶️ {t['role']} – {t['task'][:60]}…")
                    res, sc = self._execute(t)
                    self.ws.save_result(t["id"], res, sc)
                if pending_seq:
                    self.ws.enqueue(pending_seq)

            state = self.ws.read()
            new = self.plan.revise_plan(state)
            for x in new:
                x["id"] = WS.new_id(x["role"])
                x.setdefault("priority", 0)
                x.setdefault("created_at", time.time())
                x.setdefault("depends_on", [])
            if not new:
                break
            self.ws.enqueue(new)
            _log(f"📝 Planner appended {len(new)} task(s)")

        # Final synthesis (optional)
        state = self.ws.read()
        final_report = ""
        try:
            final_report = self.synth.run(self.idea, state.get("results", {}))
            self.ws.patch({"final_report": final_report})
            _log("✅ synthesis complete")
        except Exception:
            pass

        return self.ws.read(), final_report
