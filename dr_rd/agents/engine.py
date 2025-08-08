import hashlib
from typing import Dict

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
from dr_rd.evaluation import Scorecard
from config.feature_flags import (
    EVALUATORS_ENABLED,
    EVALUATOR_WEIGHTS,
    TOT_PLANNING_ENABLED,
    REFLECTION_ENABLED,
    REFLECTION_PATIENCE,
    REFLECTION_MAX_ATTEMPTS,
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
    plan_strategy = None
    reflection = None
    role_overrides: Dict[str, Dict[str, str]] = {}
    # expose to helper methods if they access via self
    setattr(self, "role_overrides", role_overrides)
    if TOT_PLANNING_ENABLED:
        from dr_rd.planning.strategies import tot  # noqa: F401
        cls = PlannerStrategyRegistry.get("tot")
        if cls:
            plan_strategy = cls()

    if REFLECTION_ENABLED:
        refl_cls = MetaAgentRegistry.get("reflector")
        if refl_cls:
            reflection = refl_cls()

    best_score = 0.0
    no_improve = 0
    history = []
    reflection_attempts = 0

    # Seed initial tasks if first run
    if not ws.read()["tasks"]:
        if plan_strategy:
            init_tasks = [
                {
                    "role": t["role"],
                    "task": t["task"],
                    "id": hashlib.sha1((t["role"] + t["task"]).encode()).hexdigest()[:10],
                    "status": "todo",
                }
                for t in plan_strategy.plan({"idea": idea})
            ]
        else:
            seed = planner.run(idea, "Develop a plan")
            init_tasks = [
                {
                    "role": role,
                    "task": task,
                    "id": hashlib.sha1((role + task).encode()).hexdigest()[:10],
                    "status": "todo",
                }
                for role, task in seed.items()
            ]
        ws.enqueue(init_tasks)
        ws.log("📝 Initial planning done")

    # HRM‐style plan → execute → revise loop
    for cycle in range(MAX_CYCLES):
        ws.patch({"cycle": cycle})
        ws.log(f"🔄 Cycle {cycle+1} start")

        # 1) Execute all tasks in current queue
        task_scores = []
        sim_failures = 0
        while True:
            t = ws.pop()
            if not t:
                break
            ws.log(f"▶️ Executing {t['role']}: {t['task']}")
            override = role_overrides.get(t["role"])
            try:
                result, score = self.run_domain_expert(t["role"], t["task"], override)
            except TypeError:
                # Backwards compatibility for implementations without override param
                if override:
                    agent = getattr(self, "agents", {}).get(t["role"])
                    if agent:
                        if override.get("system"):
                            agent.system_message += "\n" + override["system"]
                        if override.get("instructions"):
                            agent.user_prompt_template += "\n" + override["instructions"]
                result, score = self.run_domain_expert(t["role"], t["task"])
            ws.save_result(t["id"], result, score)
            ws.log(f"✔️ {t['role']} score={score:.2f}")
            # optional simulation refinement
            if self.simulation_enabled:
                try:
                    result2, score2 = simulator.refine_design(result)
                    ws.save_result(t["id"], result2, score2)
                    ws.log(f"🔄 Refined score={score2:.2f}")
                    score = max(score, score2)
                except Exception:
                    sim_failures += 1
                    ws.log("⚠️ Simulation failed")
            task_scores.append(score)

        # Optional evaluator scorecard
        state = ws.read()
        if EVALUATORS_ENABLED:
            from dr_rd import evaluators  # noqa: F401

            names = EvaluatorRegistry.list()
            if names:
                results = {}
                for name in names:
                    cls = EvaluatorRegistry.get(name)
                    try:
                        evaluator = cls()
                        data = evaluator.evaluate(state)
                        results[name] = {
                            "score": float(data.get("score", 0.0)),
                            "notes": data.get("notes", []),
                        }
                    except Exception:  # pragma: no cover - defensive
                        continue
                scorecard = Scorecard(EVALUATOR_WEIGHTS).aggregate(results)
                ws.patch({"scorecard": scorecard})
                state["scorecard"] = scorecard
                ws.log(f"📊 Scorecard overall={scorecard['overall']:.2f}")
            else:
                ws.log("⚠️ EVALUATORS_ENABLED but no evaluators registered")
        # 2) Assess improvement
        cycle_best = max(task_scores or [0.0])
        improvement = cycle_best - best_score
        if improvement < IMPROVE_THRESH:
            no_improve += 1
        else:
            best_score = cycle_best
            no_improve = 0
        ws.log(f"📈 Best score={best_score:.2f}, no_improve={no_improve}")
        history.append({"cycle": cycle, "score": cycle_best, "sim_failures": sim_failures})

        # 3) Check halting / reflection
        if no_improve > NO_PROGRESS_PATIENCE:
            if (
                REFLECTION_ENABLED
                and reflection
                and reflection_attempts < REFLECTION_MAX_ATTEMPTS
                and no_improve >= REFLECTION_PATIENCE
            ):
                ws.log("🪞 Reflecting due to stagnation")
                adjustments = reflection.reflect(history)
                reason = adjustments.get("reason", "no reason provided")
                ws.log(f"🔧 Reflection suggested: {reason}")
                if adjustments.get("switch_to_tot"):
                    from dr_rd.planning.strategies import tot  # noqa: F401
                    cls = PlannerStrategyRegistry.get("tot")
                    if cls:
                        plan_strategy = cls()
                        ws.log("🔀 Planner strategy switched to ToT")
                if adjustments.get("new_tasks"):
                    new_tasks = [
                        {
                            "role": t["role"],
                            "task": t["task"],
                            "id": hashlib.sha1((t["role"] + t["task"]).encode()).hexdigest()[:10],
                            "status": "todo",
                        }
                        for t in adjustments["new_tasks"]
                    ]
                    ws.enqueue(new_tasks)
                    ws.log(f"📝 Reflection added {len(new_tasks)} task(s)")
                if adjustments.get("role_tweak"):
                    applied = []
                    tweaks = adjustments["role_tweak"]
                    for name, tweak in tweaks.items():
                        entry = role_overrides.setdefault(name, {})
                        if isinstance(tweak, dict):
                            if "system" in tweak:
                                entry["system"] = (
                                    (entry.get("system", "") + "\n" + tweak["system"]).strip()
                                )
                            if "instructions" in tweak:
                                entry["instructions"] = (
                                    (entry.get("instructions", "") + "\n" + tweak["instructions"]).strip()
                                )
                        else:
                            entry["instructions"] = (
                                (entry.get("instructions", "") + "\n" + str(tweak)).strip()
                            )
                        applied.append(name)
                    if applied:
                        ws.log(
                            f"Reflection: applied role_tweak to {len(applied)} roles: {', '.join(applied)}"
                        )
                reflection_attempts += 1
                no_improve = 0
            else:
                ws.log("💀 Halting early due to stagnation")
                break

        # 4) Revise plan
        state = ws.read()
        if plan_strategy:
            new_tasks = plan_strategy.plan(state)
        else:
            new_tasks = planner.revise_plan(state)
        ws.enqueue(new_tasks)
        ws.log(f"📝 Planner added {len(new_tasks)} tasks")

    # 5) Synthesize final proposal from workspace results
    final_results = ws.read()["results"]
    synthesizer.run(idea, final_results)
