"""HRM engine using FirestoreWorkspace and specialized agents."""
from __future__ import annotations

from typing import Tuple

from dr_rd.utils.firestore_workspace import FirestoreWorkspace as WS
from agents import initialize_agents


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
    def run(self, max_cycles: int = 5) -> None:
        # Seed initial tasks
        if not self.ws.read()["tasks"]:
            seed = self.plan.run(self.idea, "Develop a plan")
            first = [
                {"id": WS.new_id(role), "role": role, "task": t, "status": "todo"}
                for role, t in seed.items()
            ]
            self.ws.enqueue(first)
            self.ws.log(f"🌱 seeded {len(first)} tasks from PlannerAgent")

        for cycle in range(max_cycles):
            self.ws.patch({"cycle": cycle})
            while True:
                t = self.ws.pop()
                if not t:
                    break
                self.ws.log(f"▶️ {t['role']} – {t['task'][:60]}…")
                res, sc = self._execute(t)
                self.ws.save_result(t["id"], res, sc)

            state = self.ws.read()
            new = self.plan.revise_plan(state)
            for x in new:
                x["id"] = WS.new_id(x["role"])
            if not new:
                break
            self.ws.enqueue(new)
            self.ws.log(f"📝 Planner appended {len(new)} task(s)")

        # Final synthesis (optional)
        state = self.ws.read()
        try:
            self.synth.run(self.idea, state.get("results", {}))
            self.ws.log("✅ synthesis complete")
        except Exception:
            pass
