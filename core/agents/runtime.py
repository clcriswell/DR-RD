import inspect
from typing import Any

from utils import trace_writer


def invoke_agent_safely(agent: Any, task: dict, model: Any = None, meta: Any = None):
    """Invoke *agent* with kwargs matching its signature.

    Preference order for callables: ``__call__`` → ``run`` → ``act``.
    Only parameters explicitly declared on the callable are passed.  Supported
    names are grouped as:

    - task-like: ``task``, ``input``, ``spec``, ``params`` → ``task``
    - model-like: ``model``, ``llm``, ``client`` → ``model``
    - meta-like: ``meta``, ``ctx``, ``context`` → ``meta``
    """

    fn = None
    for name in ("__call__", "run", "act"):
        candidate = getattr(agent, name, None)
        if callable(candidate):
            fn = candidate
            break
    if fn is None:
        role = task.get("role") if isinstance(task, dict) else None
        task_id = task.get("id") if isinstance(task, dict) else None
        try:
            trace_writer.append_step(
                "",
                {
                    "phase": "executor",
                    "event": "agent_error",
                    "role": role,
                    "task_id": task_id,
                    "error": "uncallable agent",
                },
            )
        except Exception:
            pass
        raise RuntimeError("uncallable agent")

    sig = inspect.signature(fn)
    mapping: dict[str, Any] = {}
    task_dict = task if isinstance(task, dict) else {}
    for name in sig.parameters:
        if name == "self":
            continue
        if name in {"task", "input", "spec", "params"}:
            mapping[name] = task
        elif name in {"model", "llm", "client"}:
            mapping[name] = model
        elif name in {"meta", "ctx", "context"}:
            mapping[name] = meta
        elif name in task_dict:
            mapping[name] = task_dict.get(name)

    bound = sig.bind_partial(**mapping)
    try:
        return fn(**bound.arguments)
    except Exception as e:  # pragma: no cover - exercised in tests
        role = task.get("role") if isinstance(task, dict) else None
        task_id = task.get("id") if isinstance(task, dict) else None
        try:
            trace_writer.append_step(
                "",
                {
                    "phase": "executor",
                    "event": "agent_error",
                    "role": role,
                    "task_id": task_id,
                    "error": str(e),
                },
            )
        except Exception:
            pass
        raise


__all__ = ["invoke_agent_safely"]
