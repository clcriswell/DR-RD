"""HRM engine using FirestoreWorkspace and specialized agents."""
from __future__ import annotations

from typing import Dict, List, Tuple

# FirestoreWorkspace implementation moved to dr_rd.utils.firestore_workspace

from dr_rd.utils.firestore_workspace import FirestoreWorkspace as WS
from dr_rd.agents.planner_agent import PlannerAgent
from dr_rd.agents.simulation_agent import SimulationAgent
from dr_rd.agents.synthesizer_agent import SynthesizerAgent

# role-specific agents
from dr_rd.agents.engineer_agent import EngineerAgent
from dr_rd.agents.cto_agent import CTOAgent
from dr_rd.agents.research_scientist_agent import ResearchScientistAgent

# add others as needed…
ROLE_DISPATCH = {
    "Engineer": EngineerAgent,
    "CTO": CTOAgent,
    "Scientist": ResearchScientistAgent,
}


class HRMLoop:
    def __init__(self, project_id: str, idea: str):
        self.ws = WS(project_id)
        self.idea = idea
        self.plan = PlannerAgent()
        self.sim = SimulationAgent()
        self.synth = SynthesizerAgent()
        # store idea once
        if not self.ws.read().get("idea"):
            self.ws.patch({"idea": idea})

    # ---------- execution helpers ----------
    def _execute(self, task: dict) -> Tuple[dict, float]:
        role_cls = ROLE_DISPATCH.get(task["role"])
        if not role_cls:
            raise ValueError(f"No agent for role {task['role']}")
        agent = role_cls()
        result, score = agent.run(task["task"])
        # --- simulation & refinement ---
        for _ in range(2):
            sim_pass, sim_metrics = self.sim.validate(result)
            if sim_pass:
                break
            result, score = agent.refine(task["task"], sim_metrics)
        return result, score

    # ---------- main loop ----------
    def run(self, max_cycles: int = 5) -> None:
        # Seed initial tasks
        if not self.ws.read()["tasks"]:
            seed = self.plan.generate_plan(self.idea)
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
