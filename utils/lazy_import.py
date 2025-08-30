import importlib
import types
from typing import Optional


class LazyModule(types.ModuleType):
    """Proxy module that loads the real module on first attribute access."""

    def __init__(self, name: str):
        super().__init__(name)
        self._name = name
        self._mod: Optional[types.ModuleType] = None

    def _load(self) -> types.ModuleType:
        if self._mod is None:
            self._mod = importlib.import_module(self._name)
            self.__dict__.update(self._mod.__dict__)
        return self._mod

    def __getattr__(self, item):  # pragma: no cover - simple delegation
        return getattr(self._load(), item)


def lazy(name: str) -> LazyModule:
    """Return a lazily imported module wrapper."""
    return LazyModule(name)


def local_import(name: str):
    """Explicitly import *name* within a function body."""
    return importlib.import_module(name)
