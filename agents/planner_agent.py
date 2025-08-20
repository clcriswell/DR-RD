"""Compatibility shim that aliases to :mod:`dr_rd.agents.planner_agent`."""
import importlib
import sys
_impl = importlib.import_module("dr_rd.agents.planner_agent")
sys.modules[__name__] = _impl
