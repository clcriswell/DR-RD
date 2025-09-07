import json
import logging
import re
from pathlib import Path
from typing import Callable, Tuple
import re

import jsonschema
from jsonschema import ValidationError

from utils import trace_writer
from utils.agent_json import extract_json_block
from utils.json_safety import parse_json_loose
from utils.logging import log_self_check

logger = logging.getLogger(__name__)

REQUIRED_KEYS = ["role", "task", "findings", "risks", "next_steps", "sources"]

_SCHEMA_CACHE: dict[str, dict | None] = {}


def _load_schema(role: str) -> dict | None:
    if role in _SCHEMA_CACHE:
        return _SCHEMA_CACHE[role]
    try:  # lazy import to avoid heavy registry cost
        from dr_rd.prompting.prompt_registry import registry

        tpl = registry.get(role)
        ref = getattr(tpl, "io_schema_ref", None) if tpl else None
        if ref:
            path = Path(ref)
            with path.open(encoding="utf-8") as fh:
                schema = json.load(fh)
            _SCHEMA_CACHE[role] = schema
            return schema
    except Exception:
        logger.debug("schema load failed for %s", role)
    _SCHEMA_CACHE[role] = None
    return None


def _missing_keys(data: dict) -> list[str]:
    missing: list[str] = []
    for k in REQUIRED_KEYS:
        if k not in data:
            missing.append(k)
            continue
        v = data[k]
        if k == "sources":
            if not isinstance(v, list):
                missing.append(k)
        else:
            if isinstance(v, str):
                if v.strip() == "":
                    missing.append(k)
            elif isinstance(v, (list, dict)):
                if len(v) == 0:
                    missing.append(k)
            elif not v:
                missing.append(k)
    return missing


def _has_required(data: dict) -> bool:
    return not _missing_keys(data)


def validate_and_retry(
    agent_name: str,
    task: dict,
    raw_text: str,
    retry_fn: Callable[[str], str],
    *,
    run_id: str | None = None,
    support_id: str | None = None,
) -> Tuple[object, dict]:
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
    escalated = False

    if not isinstance(raw_text, str):
        raw_text = json.dumps(raw_text, ensure_ascii=False)

    head = (raw_text or "")[:256]

    def _replace_todo(data: dict) -> dict:
        for k, v in list(data.items()):
            if isinstance(v, str) and v == "TODO":
                data[k] = "Not determined"
            elif isinstance(v, list):
                data[k] = ["Not determined" if i == "TODO" else i for i in v]
            elif isinstance(v, dict):
                data[k] = _replace_todo(v)
        return data

    def _check(text: object) -> tuple[bool, str, list[str]]:
        obj = text if isinstance(text, (dict, list)) else extract_json_block(text)
        candidate = obj if obj is not None else text
        if not isinstance(candidate, str):
            candidate = json.dumps(candidate, ensure_ascii=False)
        try:
            data = parse_json_loose(candidate)
        except Exception as e:
            errors.append(str(e))
            return False, candidate, []
        missing = _missing_keys(data)
        if missing:
            errors.append(f"missing_keys:{missing}")
            return False, json.dumps(data, ensure_ascii=False), missing
        schema = _load_schema(agent_name)
        if schema:
            validator = jsonschema.Draft7Validator(schema)
            schema_errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
            if schema_errors:
                for e in schema_errors:
                    errors.append(f"schema:{e.message}")
                return False, json.dumps(data, ensure_ascii=False), []
        data = _replace_todo(data)
        return True, json.dumps(data, ensure_ascii=False), []

    missing_keys: list[str] = []
    valid, raw_text, missing_keys = _check(raw_text)
    if not valid:
        retried = True
        issues: list[str] = []
        seen: set[str] = set()

        for k in missing_keys:
            issue = f"missing '{k}'"
            issues.append(issue)
            seen.add(issue)

        for err in errors:
            if not err.startswith("schema:"):
                continue
            msg = err.split("schema:", 1)[1]
            if m := re.search(r"'([^']+)' is a required property", msg):
                issue = f"missing '{m.group(1)}'"
                if issue not in seen:
                    issues.append(issue)
                    seen.add(issue)
                continue
            if "is not of type 'string'" in msg:
                inst = msg.split(" is not of type", 1)[0].strip()
                if inst.startswith("["):
                    issue = "used a list where a single string was required"
                elif inst.startswith("{"):
                    issue = "used an object where a single string was required"
                else:
                    continue
                if issue not in seen:
                    issues.append(issue)
                    seen.add(issue)
                continue
            if "is not of type 'array'" in msg:
                inst = msg.split(" is not of type", 1)[0].strip()
                if inst.startswith("'"):
                    issue = "used a string where an array was required"
                elif inst.startswith("{"):
                    issue = "used an object where an array was required"
                else:
                    issue = "used a non-array where an array was required"
                if issue not in seen:
                    issues.append(issue)
                    seen.add(issue)
                continue
            if "is not of type 'object'" in msg:
                inst = msg.split(" is not of type", 1)[0].strip()
                if inst.startswith("["):
                    issue = "used an array where an object was required"
                else:
                    issue = "used a non-object where an object was required"
                if issue not in seen:
                    issues.append(issue)
                    seen.add(issue)
                continue
            if "is not of type 'number'" in msg:
                if "'Not determined'" in msg:
                    issue = "used 'Not determined' for a numeric field"
                else:
                    issue = "used a non-numeric value where a number was required"
                if issue not in seen:
                    issues.append(issue)
                    seen.add(issue)

        if issues:
            joined = " and ".join(issues)
            fix = "these issues" if len(issues) > 1 else "this issue"
            reminder = (
                f"Reminder: Your last output was {joined}. "
                f"Fix {fix} and return a valid JSON."
            )
        else:
            reminder = (
                "Reminder: Return only the JSON object with keys role, task, "
                "findings, risks, next_steps, and sources."
            )

        try:
            if run_id:
                trace_writer.append_step(
                    run_id,
                    {
                        "phase": "executor",
                        "event": "retry_prompt",
                        "role": agent_name,
                        "task_id": task.get("id"),
                        "prompt": reminder,
                    },
                )
        except Exception:
            pass
        logger.info("retry_prompt", extra={"role": agent_name, "prompt": reminder})
        try:
            second = retry_fn(reminder)
        except Exception as e:  # pragma: no cover - retry best effort
            logger.warning("Retry failed for %s: %s", agent_name, e)
            second = raw_text
        if not isinstance(second, str):
            second = json.dumps(second, ensure_ascii=False)
        valid, raw_text, missing_keys = _check(second)
        if not valid:
            final_reminder = (
                "Final attempt: Summarize your output in one paragraph; "
                "convert any lists to semicolon-separated strings so the JSON schema is satisfied."
            )
            try:
                if run_id:
                    trace_writer.append_step(
                        run_id,
                        {
                            "phase": "executor",
                            "event": "final_retry_prompt",
                            "role": agent_name,
                            "attempt": 2,
                            "task_id": task.get("id"),
                            "prompt": final_reminder,
                        },
                    )
            except Exception:
                pass
            logger.info(
                "final_retry_prompt",
                extra={"role": agent_name, "prompt": final_reminder},
            )
            try:
                third = retry_fn(final_reminder)
            except Exception as e:  # pragma: no cover - retry best effort
                logger.warning("Final retry failed for %s: %s", agent_name, e)
                third = raw_text
            if not isinstance(third, str):
                third = json.dumps(third, ensure_ascii=False)
            valid, raw_text, missing_keys = _check(third)
            if not valid:
                escalated = True

    info = {
        "retried": retried,
        "valid_json": valid,
        "role": agent_name,
        "task": task.get("title"),
        "escalated": escalated,
    }
    logger.info("self_check", extra=info)
    if not valid:
        meta = {
            "retried": retried,
            "valid_json": False,
            "missing_keys": missing_keys,
            "escalated": escalated,
        }
        try:
            if run_id:
                trace_writer.append_step(
                    run_id,
                    {
                        "phase": "executor",
                        "event": "validation_error",
                        "role": agent_name,
                        "task_id": task.get("id"),
                        "valid_json": False,
                        "errors": errors,
                        "escalated": escalated,
                        "missing_keys": missing_keys,
                    },
                )
        except Exception:
            pass
        placeholder = {k: "Not determined" for k in REQUIRED_KEYS}
        try:
            log_self_check(run_id, support_id, {"valid_json": False, "errors": errors}, head)
        except Exception:
            pass
        return placeholder, meta
    log_self_check(run_id, support_id, {"valid_json": True}, head)
    meta = {
        "retried": retried,
        "valid_json": True,
        "missing_keys": missing_keys,
        "escalated": escalated,
    }
    return raw_text, meta
