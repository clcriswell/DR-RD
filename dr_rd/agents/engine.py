import hashlib

from dr_rd.utils.firestore_workspace import FirestoreWorkspace
from dr_rd.agents.planner_agent import PlannerAgent
from dr_rd.agents.simulation_agent import SimulationAgent
from dr_rd.agents.synthesizer_agent import SynthesizerAgent
from dr_rd.extensions.registry import (
    EvaluatorRegistry,
    PlannerStrategyRegistry,
    SimulatorRegistry,
    MetaAgentRegistry,
)

# HRM‐loop parameters
MAX_CYCLES = 5
IMPROVE_THRESH = 0.01
NO_PROGRESS_PATIENCE = 1

def run_pipeline(self, project_id: str, idea: str):
    # Initialize workspace and agents
    ws = FirestoreWorkspace(project_id)
    planner = PlannerAgent()
    simulator = SimulationAgent()
    synthesizer = SynthesizerAgent()

    best_score = 0.0
    no_improve = 0

    # Seed initial tasks if first run
    if not ws.read()["tasks"]:
        init_tasks = [
            {"role": role, "task": task, "id": hashlib.sha1((role+task).encode()).hexdigest()[:10], "status": "todo"}
            for role, task in planner.generate_plan(idea).items()
        ]
        ws.enqueue(init_tasks)
        ws.log("📝 Initial planning done")

    # HRM‐style plan → execute → revise loop
    for cycle in range(MAX_CYCLES):
        ws.patch({"cycle": cycle})
        ws.log(f"🔄 Cycle {cycle+1} start")

        # 1) Execute all tasks in current queue
        task_scores = []
        while True:
            t = ws.pop()
            if not t:
                break
            ws.log(f"▶️ Executing {t['role']}: {t['task']}")
            result, score = self.run_domain_expert(t["role"], t["task"])
            ws.save_result(t["id"], result, score)
            ws.log(f"✔️ {t['role']} score={score:.2f}")
            # optional simulation refinement
            if self.simulation_enabled:
                result2, score2 = simulator.refine_design(result)
                ws.save_result(t["id"], result2, score2)
                ws.log(f"🔄 Refined score={score2:.2f}")
                score = max(score, score2)
            task_scores.append(score)

        # 2) Assess improvement
        cycle_best = max(task_scores or [0.0])
        improvement = cycle_best - best_score
        if improvement < IMPROVE_THRESH:
            no_improve += 1
        else:
            best_score = cycle_best
            no_improve = 0
        ws.log(f"📈 Best score={best_score:.2f}, no_improve={no_improve}")

        # 3) Check halting
        if no_improve > NO_PROGRESS_PATIENCE:
            ws.log("💀 Halting early due to stagnation")
            break

        # 4) Revise plan
        state = ws.read()
        new_tasks = planner.revise_plan(state)
        ws.enqueue(new_tasks)
        ws.log(f"📝 Planner added {len(new_tasks)} tasks")

    # 5) Synthesize final proposal from workspace results
    final_results = ws.read()["results"]
    synthesizer.run(idea, final_results)
