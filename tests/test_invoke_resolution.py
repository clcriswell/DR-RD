from core.agents.invoke import resolve_invoker


class RunAgent:
    def run(self):
        pass

    def invoke(self):
        pass

    def __call__(self):
        pass


class InvokeAgent:
    def invoke(self):
        pass

    def __call__(self):
        pass


class CallAgent:
    def __call__(self):
        pass


def test_resolution_preference():
    name, _ = resolve_invoker(RunAgent())
    assert name == "run"
    name, _ = resolve_invoker(InvokeAgent())
    assert name == "invoke"
    name, _ = resolve_invoker(CallAgent())
    assert name == "__call__"
