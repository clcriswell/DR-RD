from unittest.mock import patch, Mock

import core.orchestrator as orch


def test_orchestrator_iterative_loop_executes_all_roles():
    class DummyPlanner:
        def __init__(self, *args, **kwargs):
            self.called = False

        def run(self, idea, prompt):
            return {
                "Marketing Analyst": "analyze market",
                "IP Analyst": "search patents",
                "Finance": "calc budget",
                "Research": "general research",
            }

        def revise_plan(self, state):
            if not self.called:
                self.called = True
                return [{"role": "Research", "task": "extra"}]
            return []

    class StubAgent:
        def __init__(self, name):
            self.name = name

        def act(self, idea, task, context):
            return {"findings": [f"{self.name}:{task}"], "usage": {"total_tokens": 1}}

    def fake_build_agents(mode):
        return {
            "Marketing Analyst": StubAgent("Marketing Analyst"),
            "IP Analyst": StubAgent("IP Analyst"),
            "Finance": StubAgent("Finance"),
            "Research": StubAgent("Research"),
        }

    with patch.object(orch, "PlannerAgent", DummyPlanner), \
         patch.object(orch, "build_agents", fake_build_agents), \
         patch.object(orch, "synthesize", return_value="final"), \
         patch.object(orch, "load_mode_models", return_value={"Planner": "x", "synth": "x", "default": "x"}):
        final, results, trace = orch.run_pipeline("idea", mode="test")

    assert set(results.keys()) >= {"Marketing Analyst", "IP Analyst", "Finance", "Research"}
    assert len(results["Research"]) == 2  # initial + follow-up
    assert len(trace) == 5  # 4 initial tasks + 1 follow-up
