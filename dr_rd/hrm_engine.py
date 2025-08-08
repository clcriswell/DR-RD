"""HRM engine using FirestoreWorkspace and specialized agents."""
from __future__ import annotations

from typing import Tuple, Callable, Optional, Dict, Any, List

import time

from config import MAX_CONCURRENCY
import config.feature_flags as ff
from dr_rd.engine.executor import run_tasks

from dr_rd.utils.firestore_workspace import FirestoreWorkspace as WS
from agents import initialize_agents
from dr_rd.evaluation import Scorecard
from dr_rd.extensions.registry import (
    EvaluatorRegistry,
    PlannerStrategyRegistry,
    SimulatorRegistry,
    MetaAgentRegistry,
)

EVALUATORS_ENABLED = ff.EVALUATORS_ENABLED
EVALUATOR_WEIGHTS = ff.EVALUATOR_WEIGHTS
PARALLEL_EXEC_ENABLED = ff.PARALLEL_EXEC_ENABLED
TOT_PLANNING_ENABLED = ff.TOT_PLANNING_ENABLED


class HRMLoop:
    def __init__(self, project_id: str, idea: str, flags: Optional[Dict[str, Any]] = None):
        global EVALUATORS_ENABLED, PARALLEL_EXEC_ENABLED, TOT_PLANNING_ENABLED
        if flags:
            for k, v in flags.items():
                setattr(ff, k, v)
            EVALUATORS_ENABLED = ff.EVALUATORS_ENABLED
            PARALLEL_EXEC_ENABLED = ff.PARALLEL_EXEC_ENABLED
            TOT_PLANNING_ENABLED = ff.TOT_PLANNING_ENABLED
        self.ws = WS(project_id)
        self.idea = idea
        self.agents = initialize_agents()
        self.plan = self.agents["Planner"]
        self.synth = self.agents["Synthesizer"]
        try:
            from dr_rd.agents.hrm_agent import HRMAgent
            from dr_rd.evaluators import (
                feasibility_ev,
                clarity_ev,
                coherence_ev,
                goal_fit_ev,
            )
            from dr_rd.config.feature_flags import (
                AGENT_HRM_ENABLED,
                AGENT_TOPK,
                AGENT_MAX_RETRIES,
                AGENT_THRESHOLD,
            )
            if AGENT_HRM_ENABLED:
                self.plan = HRMAgent(
                    self.plan,
                    [feasibility_ev, clarity_ev],
                    self.ws,
                    "Planner",
                    top_k=AGENT_TOPK,
                    max_retries=AGENT_MAX_RETRIES,
                    threshold=AGENT_THRESHOLD,
                )
                self.synth = HRMAgent(
                    self.synth,
                    [coherence_ev, goal_fit_ev],
                    self.ws,
                    "Synthesizer",
                    top_k=AGENT_TOPK,
                    max_retries=AGENT_MAX_RETRIES,
                    threshold=AGENT_THRESHOLD,
                )
                self.agents["Planner"] = self.plan
                self.agents["Synthesizer"] = self.synth
        except Exception:
            pass
        self.plan_strategy = None
        if TOT_PLANNING_ENABLED:
            # Import lazily so default runs stay fast
            from dr_rd.planning.strategies import tot  # noqa: F401

            cls = PlannerStrategyRegistry.get("tot")
            if cls:
                self.plan_strategy = cls()
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
            if self.plan_strategy:
                seed_tasks = self.plan_strategy.plan(self.ws.read())
                first = [
                    {
                        "id": WS.new_id(t["role"]),
                        "role": t["role"],
                        "task": t["task"],
                        "status": "todo",
                        "priority": 0,
                        "created_at": time.time(),
                        "depends_on": [],
                    }
                    for t in seed_tasks
                ]
                self.ws.enqueue(first)
                _log(f"🌱 seeded {len(first)} tasks from ToTPlannerStrategy")
            else:
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
            scorecard = None
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
                    self.ws.patch({"scorecard": scorecard})
                    state["scorecard"] = scorecard
                    _log(f"📊 scorecard overall={scorecard['overall']:.2f}")
                else:
                    _log("⚠️ EVALUATORS_ENABLED but no evaluators registered")

            if self.plan_strategy:
                new = self.plan_strategy.plan(state)
            else:
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

    @staticmethod
    def plan_from_brief(brief: dict):
        """Return a list of tasks extracted from a brief."""
        try:
            from agents.planner_agent import PlannerAgent
            from config.agent_models import AGENT_MODEL_MAP
            idea = brief.get("idea", "")
            planner = PlannerAgent(AGENT_MODEL_MAP.get("Planner", ""))
            plan = planner.run(idea, "Break down the project into role-specific tasks")
            return [{"role": r, "task": t} for r, t in plan.items()]
        except Exception:
            return []

    @staticmethod
    def evaluate_results(results):
        """Aggregate evaluator scores into a simple average."""
        from dr_rd.evaluators import feasibility_ev, clarity_ev, coherence_ev

        notes, scores = [], []
        coverage_confidence = float(results.get("coverage_confidence", 0.0)) if isinstance(results, dict) else 0.0
        for ev in (feasibility_ev, clarity_ev, coherence_ev):
            try:
                s = float(ev(results, {}))
            except Exception:
                s = 0.0
            scores.append(s)
            notes.append(f"{ev.__name__}: {s:.2f}")
        avg = sum(scores) / len(scores) if scores else 0.0
        return {"score": avg, "notes": notes, "coverage_confidence": coverage_confidence}

    @staticmethod
    def get_help(brief, context=None):
        """Return a list of advice strings."""
        return [
            {"note": "Consult patent X re: method Y"},
            {"note": "See arXiv:ZZZ for baseline metrics"},
        ]


def run(idea: str) -> Dict[str, Any]:
    """Run a minimal one-cycle HRM loop with all features disabled.

    This convenience helper patches the workspace and agent initialization with
    lightweight in-memory implementations so the loop can execute without
    external services. All feature flags are forced to ``False`` to ensure a
    fast smoke-test style run. The dictionary of results produced by the
    cycle is returned.
    """

    import hashlib
    import importlib
    import os
    from typing import Any, Dict

    # Ensure feature flags are disabled regardless of environment variables
    global EVALUATORS_ENABLED, PARALLEL_EXEC_ENABLED, TOT_PLANNING_ENABLED
    global REFLECTION_ENABLED, SIM_OPTIMIZER_ENABLED, RAG_ENABLED
    EVALUATORS_ENABLED = False
    PARALLEL_EXEC_ENABLED = False
    TOT_PLANNING_ENABLED = False
    REFLECTION_ENABLED = False
    SIM_OPTIMIZER_ENABLED = False
    RAG_ENABLED = False
    for name in [
        "EVALUATORS_ENABLED",
        "PARALLEL_EXEC_ENABLED",
        "TOT_PLANNING_ENABLED",
        "REFLECTION_ENABLED",
        "SIM_OPTIMIZER_ENABLED",
        "RAG_ENABLED",
    ]:
        os.environ.pop(name, None)
    import config.feature_flags as ff
    importlib.reload(ff)

    # In-memory workspace avoiding Firestore
    class _WS:
        def __init__(self, project_id: str):  # pragma: no cover - simple storage
            self.data = {
                "idea": "",
                "tasks": [],
                "results": {},
                "scores": {},
                "history": [],
                "cycle": 0,
            }

        def read(self) -> Dict[str, Any]:
            return {
                k: (v.copy() if isinstance(v, (dict, list)) else v)
                for k, v in self.data.items()
            }

        def patch(self, d: Dict[str, Any]) -> None:
            self.data.update(d)

        def enqueue(self, tasks: List[Dict[str, Any]]) -> None:
            self.data["tasks"].extend(tasks)

        def pop(self) -> Optional[Dict[str, Any]]:
            return self.data["tasks"].pop(0) if self.data["tasks"] else None

        def save_result(self, tid: str, result: Any, score: float) -> None:
            self.data["results"][tid] = result
            self.data["scores"][tid] = score

        def log(self, msg: str) -> None:
            pass

        @staticmethod
        def new_id(role: str) -> str:
            return hashlib.sha1(f"{role}{time.time()}".encode()).hexdigest()[:10]

    # Minimal agent implementations
    class _Planner:
        def run(self, idea: str, prompt: str) -> Dict[str, str]:
            return {"Worker": "do work"}

        def revise_plan(self, state: Dict[str, Any]) -> List[Dict[str, str]]:
            return []

    class _Worker:
        def run(self, idea: str, task: str) -> Dict[str, Any]:
            return {"output": "done"}

    class _Synth:
        def run(self, idea: str, results: Dict[str, Any]) -> str:
            return "ok"

    def _init_agents() -> Dict[str, Any]:
        return {"Planner": _Planner(), "Worker": _Worker(), "Synthesizer": _Synth()}

    # Patch globals so HRMLoop uses the lightweight components
    original_ws, original_init = WS, initialize_agents
    globals()["WS"] = _WS
    globals()["initialize_agents"] = _init_agents
    try:
        loop = HRMLoop("smoke", idea)
        state, _ = loop.run(max_cycles=1)
    finally:
        globals()["WS"] = original_ws
        globals()["initialize_agents"] = original_init

    return state.get("results", {})
