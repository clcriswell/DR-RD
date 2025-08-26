"""Optional AutoGen-based orchestrator."""
from __future__ import annotations

from typing import Any, Dict, Tuple

import config.feature_flags as ff


def run_autogen(prompt: str, max_turns: int = 2) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
    """Run a tiny AutoGen conversation.

    The implementation is purposely lightweight. If the ``autogen`` package is
    not installed the function raises ``RuntimeError``.
    """
    if not ff.AUTOGEN_ENABLED:
        raise RuntimeError("AUTOGEN_ENABLED is false")

    try:  # pragma: no cover - optional dependency
        import autogen  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("autogen package not available") from exc

    # Minimal two-agent exchange using autogen's ConversableAgent
    trace = []
    user = autogen.ConversableAgent("user")
    assistant = autogen.ConversableAgent("assistant")
    user.initiate_chat(assistant, message=prompt)
    turns = 0
    final = ""
    while turns < max_turns:
        turns += 1
        msg = assistant.last_message()["content"] if assistant.last_message() else ""
        trace.append({"turn": turns, "message": msg})
        if not msg:
            break
        final = msg
        assistant.send(msg, user)
    return final, {}, {"autogen_trace": trace}


__all__ = ["run_autogen"]
