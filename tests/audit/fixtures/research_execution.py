class DummyAgent:
    name = "Research Scientist"

    def act(self, idea, task, context):
        return {
            "findings": ["stub"],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }


class DummyPlanner:
    def __init__(self, model):
        pass

    def run(self, idea, prompt):
        return [
            {
                "role": "Research Scientist",
                "title": "Stub task",
                "description": "do something",
            }
        ]

    def revise_plan(self, context):
        return []


def dummy_build_agents(mode, models=None):
    return {"Research Scientist": DummyAgent()}


def dummy_synthesize(idea, results, model_id=None):
    return "stub dossier"
