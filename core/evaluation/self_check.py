import json
import logging
from typing import Callable, Tuple
from utils import trace_writer

from utils.agent_json import extract_json_block

logger = logging.getLogger(__name__)

REQUIRED_KEYS = ["role", "task", "findings", "risks", "next_steps", "sources"]


def _has_required(data: dict) -> bool:
    return all(k in data for k in REQUIRED_KEYS)


def validate_and_retry(
    agent_name: str,
    task: dict,
    raw_text: str,
    retry_fn: Callable[[str], str],
    *,
    run_id: str | None = None,
) -> Tuple[str, dict]:
    """Validate ``raw_text`` for the uniform JSON contract and retry once if needed.

    Parameters
    ----------
    agent_name: str
        Name of the agent producing ``raw_text``.
    task: dict
        Original task dictionary for logging context.
    raw_text: str
        Initial agent output.
    retry_fn: Callable[[str], str]
        Callback invoked with a reminder string if a retry is required. It must
        return the agent's second attempt as text.
    """

    retried = False
    valid = False
    errors: list[str] = []

    # ``raw_text`` may be a dict if the agent returns structured data.
    if not isinstance(raw_text, str):
        raw_text = json.dumps(raw_text)

    def _check(text: str) -> bool:
        if not isinstance(text, str):
            text = json.dumps(text)
        block = extract_json_block(text)
        candidate = block if block is not None else text
        try:
            data = json.loads(candidate)
        except Exception as e:
            errors.append(str(e))
            return False
        if not _has_required(data):
            missing = [k for k in REQUIRED_KEYS if k not in data]
            errors.append(f"missing_keys:{missing}")
            return False
        return True

    valid = _check(raw_text)
    if not valid:
        retried = True
        reminder = (
            "You omitted the required JSON summary. Return only the JSON object with keys: "
            "role, task, findings, risks, next_steps, sources."
        )
        try:
            second = retry_fn(reminder)
        except Exception as e:  # pragma: no cover - retry best effort
            logger.warning("Retry failed for %s: %s", agent_name, e)
            second = raw_text
        if not isinstance(second, str):
            second = json.dumps(second)
        if _check(second):
            raw_text = second
            valid = True
    info = {"retried": retried, "valid_json": valid, "role": agent_name, "task": task.get("title")}
    logger.info("self_check=%s", info)
    if not valid:
        try:
            trace_writer.append_step(
                run_id or "",
                {
                    "phase": "executor",
                    "event": "validation_error",
                    "role": agent_name,
                    "task_id": task.get("id"),
                    "valid_json": False,
                    "errors": errors,
                },
            )
        except Exception:
            pass
        raise ValueError("Invalid JSON output")
    return raw_text, {"retried": retried, "valid_json": True}
