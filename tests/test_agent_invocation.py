from core.agents.runtime import invoke_agent_safely


class AgentTaskOnly:
    def __call__(self, task):
        return task["id"]


class AgentTaskModel:
    def __call__(self, task, model):
        return model


class AgentTaskModelMeta:
    def __call__(self, task, model, meta):
        return meta["context"]


class AgentIdeaTask:
    def run(self, idea, task):
        return f"{idea}:{task['id']}"


class AgentQA:
    def act(self, requirements, tests, defects):
        return requirements, tests, defects


def test_invocation_bindings():
    pseudo = {
        "id": "T1",
        "title": "t",
        "summary": "s",
        "description": "d",
        "role": "CTO",
        "idea": "Idea",
        "requirements": [1],
        "tests": [2],
        "defects": [3],
        "context": {},
    }
    assert invoke_agent_safely(AgentTaskOnly(), pseudo) == "T1"
    assert invoke_agent_safely(AgentTaskModel(), pseudo, model="m") == "m"
    assert (
        invoke_agent_safely(AgentTaskModelMeta(), pseudo, model="m", meta={"context": 1})
        == 1
    )
    assert invoke_agent_safely(AgentIdeaTask(), pseudo) == "Idea:T1"
    assert invoke_agent_safely(AgentQA(), pseudo) == ([1], [2], [3])
