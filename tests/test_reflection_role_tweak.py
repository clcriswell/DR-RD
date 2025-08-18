"""Tests for reflection-driven role prompt tweaks."""

from dr_rd.agents import engine


def test_role_tweak_applied(monkeypatch):
    """Next cycle should apply role_tweak overrides to prompts."""

    # Enable reflection and disable other features
    monkeypatch.setattr(engine, "REFLECTION_ENABLED", True)
    monkeypatch.setattr(engine, "TOT_PLANNING_ENABLED", False)
    monkeypatch.setattr(engine, "EVALUATORS_ENABLED", False)

    # Stub workspace storing tasks in memory
    class WS:
        def __init__(self, project_id):
            self.data = {
                "idea": "",
                "tasks": [],
                "results": {},
                "scores": {},
                "history": [],
                "cycle": 0,
            }

        def read(self):
            return {k: (v.copy() if isinstance(v, (dict, list)) else v) for k, v in self.data.items()}

        def patch(self, d):
            self.data.update(d)

        def enqueue(self, tasks):
            self.data["tasks"].extend(tasks)

        def pop(self):
            return self.data["tasks"].pop(0) if self.data["tasks"] else None

        def save_result(self, tid, result, score):
            self.data["results"][tid] = result
            self.data["scores"][tid] = score

        def log(self, msg):
            pass

    monkeypatch.setattr(engine, "FirestoreWorkspace", WS)

    # Planner stubs out plan and revise_plan
    class DummyPlanner:
        def __init__(self):
            self.count = 0

        def run(self, idea, prompt):
            return [{"role": "Engineer", "title": "do stuff", "description": "do stuff"}]

        def revise_plan(self, state):
            self.count += 1
            return [
                {"role": "Engineer", "task": "do stuff", "id": f"id{self.count}", "status": "todo"}
            ]

    monkeypatch.setattr(engine, "PlannerAgent", DummyPlanner)

    class DummySimulation:
        def refine_design(self, result):
            return result, 0.0

    class DummySynth:
        def run(self, idea, results):
            pass

    monkeypatch.setattr(engine, "SimulationAgent", DummySimulation)
    monkeypatch.setattr(engine, "SynthesizerAgent", DummySynth)

    # Reflection meta-agent emitting a role tweak once
    class DummyReflector:
        def __init__(self):
            self.called = False

        def reflect(self, history):
            if not self.called:
                self.called = True
                return {"role_tweak": {"Engineer": "extra directive"}, "reason": "plateau"}
            return {}

    monkeypatch.setattr(engine.MetaAgentRegistry, "get", lambda name: DummyReflector if name == "reflector" else None)

    # Orchestrator capturing prompts
    class Orchestrator:
        simulation_enabled = False

        def __init__(self):
            self.prompts = []

        def run_domain_expert(self, role, task, override=None):
            prompt = task
            if override and override.get("instructions"):
                prompt += " | " + override["instructions"]
            self.prompts.append(prompt)
            return "res", 0.0

    orch = Orchestrator()
    engine.run_pipeline(orch, "p1", "idea")

    # Third execution should include reflected directive
    assert orch.prompts[2].endswith("extra directive")

