class DummyQARouter:
    def __init__(self):
        self.called = False
        self.context = None

    def route_failure(self, metrics, outputs_dir, context=None):
        self.called = True
        self.context = context
