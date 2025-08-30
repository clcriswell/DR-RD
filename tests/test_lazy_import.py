from utils.lazy_import import lazy, local_import


def test_lazy_loads_and_caches(monkeypatch):
    mod = lazy("json")
    assert mod.loads('{"a":1}') == {"a": 1}

    called = []
    import importlib

    def spy(name, package=None):
        called.append(name)
        return orig(name, package)

    orig = importlib.import_module
    monkeypatch.setattr(importlib, "import_module", spy)

    mod.dumps({"b": 2})
    mod.dumps({"c": 3})
    assert called == []


def test_local_import():
    import json as builtin_json

    mod = local_import("json")
    assert mod is builtin_json
