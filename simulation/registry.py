REGISTRY = {}


def register(name: str):
    def _wrap(fn):
        REGISTRY[name] = fn
        return fn

    return _wrap


def get(name: str):
    return REGISTRY[name]
