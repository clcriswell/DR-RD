from core.agents.runtime import invoke_agent_safely


class A:
    def __call__(self, task):
        return task


class B:
    def run(self, task, model):
        return task, model


class C:
    def act(self, task, model, meta):
        return task, model, meta


class D:
    def __call__(self, spec):
        return spec


def test_invoke_agent_signatures():
    t = {"id": "t1"}
    assert invoke_agent_safely(A(), t, model="m", meta="x") == t
    assert invoke_agent_safely(B(), t, model="m", meta="x") == (t, "m")
    assert invoke_agent_safely(C(), t, model="m", meta="x") == (t, "m", "x")
    assert invoke_agent_safely(D(), {"foo": 1}) == {"foo": 1}
