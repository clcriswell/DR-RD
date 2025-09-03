import inspect
import json
import streamlit as st
from utils import trace_writer


def _resolve_callable(agent):
    for name in ("__call__", "run", "act"):
        fn = getattr(agent, name, None)
        if callable(fn):
            return fn
    return None


def invoke_agent_safely(agent, task, model=None, meta=None):
    fn = _resolve_callable(agent)
    if fn is None:
        run_id = st.session_state.get("run_id", "")
        role = task.get("role") if isinstance(task, dict) else None
        try:
            trace_writer.append_step(
                run_id,
                {
                    "phase": "executor",
                    "event": "agent_error",
                    "role": role,
                    "task_id": task.get("id") if isinstance(task, dict) else None,
                    "error": "no_callable_interface",
                },
            )
        except Exception:
            pass
        raise RuntimeError(f"{agent.__class__.__name__} has no callable interface")
    sig = inspect.signature(fn)
    params = list(sig.parameters.values())
    try:
        if len(params) == 1:
            name = params[0].name
            if name in {"spec", "payload"}:
                spec = {"task": task, "model": model, "meta": meta}
                return fn(spec)
            try:
                return fn(task)
            except TypeError:
                spec = {"task": task, "model": model, "meta": meta}
                return fn(spec)
        if len(params) == 2:
            return fn(task, model)
        if len(params) == 3:
            return fn(task, model, meta)
        spec = {"task": task, "model": model, "meta": meta}
        return fn(spec)
    except Exception as e:
        run_id = st.session_state.get("run_id", "")
        role = task.get("role") if isinstance(task, dict) else None
        try:
            trace_writer.append_step(
                run_id,
                {
                    "phase": "executor",
                    "event": "agent_error",
                    "role": role,
                    "task_id": task.get("id") if isinstance(task, dict) else None,
                    "error": str(e),
                },
            )
        except Exception:
            pass
        raise


__all__ = ["invoke_agent_safely"]
