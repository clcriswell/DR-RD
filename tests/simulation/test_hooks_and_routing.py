from simulation.simulation_manager import SimulationManager
from orchestrators import qa_router


class DummyHook:
    def __init__(self):
        self.iter_called = False
        self.complete_called = False
        self.fail_called = False

    def on_iteration(self, state):
        self.iter_called = True

    def on_complete(self, metrics, outputs_dir):
        self.complete_called = True

    def on_failure(self, metrics, outputs_dir):
        self.fail_called = True


def test_hooks_and_qa_routing(tmp_path):
    sm = SimulationManager()
    hook = DummyHook()

    class Router:
        def __init__(self):
            self.called = False

        def route_failure(self, metrics, outputs_dir, context=None):
            self.called = True
            qa_router.route_failure(metrics, outputs_dir, context)

    router = Router()
    metrics = sm.simulate("thermal", "spec", hooks=[hook], outputs_dir=tmp_path, qa_router=router)
    assert hook.iter_called
    assert hook.fail_called and not hook.complete_called
    assert router.called
    assert (tmp_path / "qa_queue.json").exists()
