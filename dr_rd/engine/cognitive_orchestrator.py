from __future__ import annotations

"""Lightweight cognitive orchestrator mimicking human problem solving."""

from dataclasses import dataclass
from typing import Any, Dict, List, Callable


@dataclass
class CogConfig:
    """Configuration for the cognitive orchestrator."""

    use_help_path: bool = True
    incubation_threads: int = 1
    max_iterations: int = 1
    success_threshold: float = 0.0


@dataclass
class CogState:
    """Mutable state tracked across orchestrator steps."""

    needs_help: bool = False
    last_score: float = 0.0


class CognitiveOrchestrator:
    """Minimal cognitive workflow controller."""

    def __init__(
        self,
        ws: Any,
        agents: Dict[str, Any],
        evaluators: List[Callable[[Dict[str, Any]], Dict[str, Any]]],
        cfg: CogConfig,
    ) -> None:
        self.ws = ws
        self.agents = agents
        self.evaluators = evaluators
        self.cfg = cfg
        self.state = CogState()

    # --- core steps -----------------------------------------------------
    def frame_problem(self) -> None:
        idea = self.ws.read().get("idea", "")
        try:
            brief = self.agents["Planner"].run(idea, "Provide a concise problem brief")
        except Exception:  # pragma: no cover - defensive
            brief = {}
        self.ws.patch({"brief": brief})
        self.ws.log("🧭 framed problem")

    def decide_self_vs_help(self) -> bool:
        coverage = float(
            self.ws.read().get("knowledge_index", {}).get("coverage_confidence", 0.0)
        )
        needs_help = bool(self.cfg.use_help_path and coverage < 0.55)
        self.state.needs_help = needs_help
        msg = "🆘 help needed" if needs_help else "💪 proceeding solo"
        self.ws.log(msg)
        return needs_help

    def seek_help(self) -> List[Dict[str, Any]]:
        inputs: List[Dict[str, Any]] = []
        for role in ("CTO", "ResearchScientist", "Engineer"):
            agent = self.agents.get(role)
            if not agent:
                continue
            try:
                notes = agent.run(
                    {
                        "task": "Provide expert guidance",
                        "context": self.ws.read(),
                    }
                )
            except Exception:  # pragma: no cover - defensive
                notes = ""
            inputs.append({"role": role, "notes": notes})
        if inputs:
            self.ws.append("external_inputs", inputs)
        self.ws.log(f"📬 gathered {len(inputs)} external inputs")
        return inputs

    def generate_candidates(self) -> List[Any]:
        idea = self.ws.read().get("idea", "")
        try:
            raw = self.agents["Planner"].run(
                idea,
                "Propose 5 distinct solution approaches",
            )
        except Exception:  # pragma: no cover - defensive
            raw = []
        if isinstance(raw, dict):
            cands = list(raw.values())
        elif isinstance(raw, list):
            cands = raw
        else:
            cands = [raw]
        cands = cands[:5]
        self.ws.patch({"candidates": cands})
        return cands

    def incubate(self) -> None:
        self.ws.log("🛌 incubation start")
        # Placeholder for lateral searches (optional)
        for _ in range(min(self.cfg.incubation_threads, 2)):
            pass
        self.ws.log("🛌 incubation done")

    def select_best(self) -> Any:
        candidates = self.ws.read().get("candidates", [])
        try:
            chosen = self.agents["Synthesizer"].run(
                {
                    "task": "Select the best candidate",
                    "candidates": candidates,
                }
            )
        except Exception:  # pragma: no cover - defensive
            chosen = candidates[0] if candidates else {}
        self.ws.patch({"chosen": chosen})
        return chosen

    def test_and_evaluate(self) -> float:
        state = self.ws.read()
        if "Simulation" in self.agents:
            try:  # pragma: no cover - defensive
                sim_res = self.agents["Simulation"].run(state)
                self.ws.patch({"simulation": sim_res})
            except Exception:
                pass
        results = []
        for fn in self.evaluators:
            try:
                data = fn(state)
            except Exception:  # pragma: no cover - defensive
                data = {"score": 0.0, "notes": []}
            results.append(data)
        scores = [r.get("score", 0.0) for r in results]
        avg = sum(scores) / len(scores) if scores else 0.0
        self.state.last_score = avg
        self.ws.patch({"evaluation": {"evaluators": results, "average_score": avg}})
        self.ws.log(f"📈 evaluation {avg:.2f}")
        return avg

    # --- driver ---------------------------------------------------------
    def run(self) -> float:
        self.frame_problem()
        if self.decide_self_vs_help():
            self.seek_help()
        self.generate_candidates()
        self.incubate()
        self.select_best()
        self.test_and_evaluate()
        return self.state.last_score
