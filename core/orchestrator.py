import json
import os
import re
from dataclasses import asdict, dataclass
from json import JSONDecodeError
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

import config.feature_flags as ff
from core.agents.evaluation_agent import EvaluationAgent
from core.agents.runtime import invoke_agent_safely
from core.agents.unified_registry import AGENT_REGISTRY
from core.evaluation.self_check import validate_and_retry
from core.llm import complete, select_model
from core.llm_client import responses_json_schema_for
from core.observability import (
    AgentTraceCollector,
    EvidenceSet,
    build_coverage,
)
from core.privacy import pseudonymize_for_model, rehydrate_output
from core.redaction import Redactor
from core.router import route_task
from core.roles import normalize_role
from core.schemas import Plan, ScopeNote
from memory.decision_log import log_decision
from orchestrators.executor import execute as exec_artifacts
from dr_rd.prompting.prompt_registry import registry
from utils import checkpoints, otel, trace_writer
from utils import safety as safety_utils
from utils.agent_json import extract_json_block, extract_json_strict
from utils.cancellation import CancellationToken
from utils.logging import logger, safe_exc
from dr_rd.agents.dynamic_agent import EmptyModelOutput


@dataclass
class AgentResult:
    text: str = ""
    payload: dict | None = None
    error: dict | None = None


def _to_text(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    return json.dumps(x, ensure_ascii=False)
from utils.paths import ensure_run_dirs
from utils.stream_events import Event
from utils.telemetry import (
    resume_failed,
    run_resumed,
    safety_flagged_step,
    stream_completed,
    stream_started,
    tasks_normalized,
    tasks_planned,
)
from utils.timeouts import Deadline, with_deadline

evidence: EvidenceSet | None = None


class ResumeNotPossible(Exception):
    pass


def _coerce_and_fill(data: dict | list) -> dict:
    """Coerce planner output into a normalized task object.

    ``data`` may be a list or dict.  Tasks are cleaned and missing fields filled
    without dropping entries unless ``title`` or ``summary`` are blank after
    stripping.  Any additional keys on task objects are preserved.
    """

    if isinstance(data, list):
        data = {"tasks": data}

    tasks = data.get("tasks") if isinstance(data, dict) else None
    if not isinstance(tasks, list):
        tasks = []

    raw_count = len(tasks)
    norm_tasks: list[dict[str, Any]] = []
    for i, t in enumerate(tasks, 1):
        if not isinstance(t, dict):
            continue
        tid = str(t.get("id") or f"T{i:02d}")
        title = (t.get("title") or "").strip()
        summary = (t.get("summary") or t.get("description") or "").strip()
        description = (t.get("description") or t.get("summary") or "").strip()
        role_raw = t.get("role")
        role = normalize_role(role_raw) or "Dynamic Specialist"
        if title == "" or summary == "":
            continue
        nt = dict(t)
        nt.update(
            {
                "id": tid,
                "title": title,
                "summary": summary,
                "description": description,
                "role": role,
            }
        )
        norm_tasks.append(nt)

    norm = {"tasks": norm_tasks, "_raw_count": raw_count}

    if raw_count > 0 and len(norm_tasks) == 0:
        dump_dir = Path("debug/logs")
        dump_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S%f")
        dump_path = dump_dir / f"planner_payload_{ts}.json"
        try:
            dump_path.write_text(json.dumps(data, indent=2))
        except Exception:
            pass
        raise ValueError("planner.normalization_zero")

    return norm


_GLOBAL_REDACTOR: Redactor | None = None


def _get_redactor() -> Redactor:
    global _GLOBAL_REDACTOR
    if _GLOBAL_REDACTOR is None:
        _GLOBAL_REDACTOR = Redactor()
    return _GLOBAL_REDACTOR


def _invoke_agent(agent, context, task, model=None):
    redactor = _get_redactor()
    if isinstance(task, str):
        task = {"title": task, "description": task}
    payload = dict(task)
    role = payload.get("role")
    red_task = {}
    for k, v in payload.items():
        if isinstance(v, str) and k != "role":
            rv, _, _ = redactor.redact(v, mode="light", role=role)
            red_task[k] = rv
        else:
            red_task[k] = v
    red_context, _, _ = redactor.redact(context, mode="light", role=role)
    alias_map = dict(redactor.alias_map)
    task["alias_map"] = alias_map
    return invoke_agent_safely(agent, task=red_task, model=model, meta=red_context)


def generate_plan(
    idea: str,
    constraints: str | None = None,
    risk_posture: str | None = None,
    ui_model: str | None = None,
    *,
    cancel: CancellationToken | None = None,
    deadline_ts: float | None = None,
    run_ctx: dict | None = None,
) -> list[dict[str, str]]:
    """Use the Planner to create and normalize a task list.

    The input idea/constraints are pre-redacted according to the redaction
    policy.  The planner output is validated against :class:`Plan`; if the
    JSON is malformed a single retry with an explicit instruction is made.
    """

    deadline = Deadline(deadline_ts)

    def _check() -> None:
        if cancel and cancel.is_set():
            raise RuntimeError("cancelled")
        if deadline and deadline.expired():
            raise TimeoutError("deadline reached")

    _check()

    run_ctx = run_ctx or {}
    redactor = run_ctx.get("redactor") or Redactor()
    run_ctx["redactor"] = redactor

    constraint_list = [c.strip() for c in (constraints or "").splitlines() if c.strip()]
    placeholders_seen: set[str] = set()
    redacted_idea, _, ph = redactor.redact(idea, mode="light", role="Planner")
    placeholders_seen.update(ph)
    redacted_constraints: list[str] = []
    for c in constraint_list:
        rc, _, ph = redactor.redact(c, mode="light", role="Planner")
        redacted_constraints.append(rc)
        placeholders_seen.update(ph)
    run_ctx["alias_map"] = redactor.alias_map
    try:
        st.session_state["alias_map"] = redactor.alias_map
    except Exception:
        pass

    sn = ScopeNote(
        idea=redacted_idea,
        constraints=redacted_constraints,
        risk_posture=(risk_posture or "medium").lower(),
        redaction_rules=[],
    )
    try:  # persist for UI tests
        st.session_state["scope_note"] = sn.model_dump()
    except Exception:
        pass

    constraints_section = (
        f"\nConstraints: {'; '.join(redacted_constraints)}" if redacted_constraints else ""
    )
    risk_section = f"\nRisk posture: {sn.risk_posture}" if risk_posture else ""

    model = select_model("planner", ui_model)

    response_format = responses_json_schema_for(Plan, "Plan")

    def _call(extra: str = "") -> list[dict[str, str]]:
        _check()
        try:
            with with_deadline(deadline):
                result = complete(
                    system_prompt,
                    user_prompt + extra,
                    model=model,
                    response_format=response_format,
                )
        except TypeError:  # backward compatibility for tests
            with with_deadline(deadline):
                result = complete(system_prompt, user_prompt + extra)
        raw = result.content or "{}"
        raw_data = extract_json_strict(raw)
        if isinstance(raw_data, list):
            raw_data = {"tasks": raw_data}
        if isinstance(raw_data, dict) and raw_data.get("error"):
            raise ValueError("planner.error_returned")
        alias_map = run_ctx.get("alias_map", redactor.alias_map)
        if alias_map:
            raw_data = rehydrate_output(raw_data, alias_map)

        norm = _coerce_and_fill(raw_data)
        raw_count = norm.pop("_raw_count", 0)
        norm_tasks = norm.get("tasks", [])
        tasks_planned(raw_count)
        tasks_normalized(len(norm_tasks))

        from pydantic import ValidationError

        try:
            Plan.model_validate(norm, strict=True)
        except ValidationError as e:
            dump_dir = Path("debug/logs")
            dump_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S%f")
            dump_path = dump_dir / f"planner_payload_{ts}.json"
            dump_path.write_text(json.dumps(raw_data, indent=2))
            logger.error(
                "planner.validation_failed",
                extra={"errors": len(e.errors()), "dump_path": str(dump_path)},
            )
            raise ValueError("missing required fields") from e

        run_id = st.session_state.get("run_id", "latest")
        try:
            run_dir = ensure_run_dirs(run_id)
            (run_dir / "plan.json").write_text(json.dumps({"tasks": norm_tasks}, indent=2))
        except Exception:
            pass
        try:
            st.session_state["plan_tasks"] = norm_tasks
            st.session_state["raw_planned_tasks"] = raw_count
            st.session_state["normalized_tasks_count"] = len(norm_tasks)
        except Exception:
            pass
        try:
            trace_writer.append_step(
                run_id,
                {
                    "phase": "planner",
                    "summary": norm_tasks,
                    "planned_tasks": raw_count,
                    "normalized_tasks": len(norm_tasks),
                },
            )
            trace_writer.flush_phase_meta(
                run_id,
                "planner",
                {"planned_tasks": raw_count, "normalized_tasks": len(norm_tasks)},
            )
        except Exception:
            pass
        if not norm_tasks:
            raise ValueError("planner.no_tasks")
        return norm_tasks

    tpl = registry.get("Planner")
    system_prompt = tpl.system
    if placeholders_seen:
        system_prompt += "\n" + redactor.note_for_placeholders(placeholders_seen)

    user_prompt = tpl.user_template.format(
        idea=sn.idea,
        constraints_section=constraints_section,
        risk_section=risk_section,
    )

    try:
        st.session_state["_last_prompt"] = (system_prompt + "\n" + user_prompt)[:4000]
    except Exception:
        pass

    try:
        return _call()
    except Exception as e:
        if isinstance(e, ValueError) and str(e).startswith("planner."):
            raise
        _check()
        try:
            msg = "\nMalformed JSON in prior response. Return valid JSON only."
            return _call(msg)
        except Exception as e2:
            raise ValueError(f"Planner JSON validation failed: {e2}") from e


def _slugify(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s[:64] or "project"


def _normalize_evidence_payload(payload: Any) -> dict[str, Any]:
    """Normalize evidence payloads of various shapes into a dict.

    Accepts dict, list[dict], list[tuple], or list[str]. Always returns a dict
    with keys: ``quotes``, ``tokens_in``, ``tokens_out``, ``citations``, ``cost``,
    and ``raw``.
    """

    quotes: list[Any] = []
    tokens_in = 0
    tokens_out = 0
    citations: list[Any] = []
    cost = 0.0

    if isinstance(payload, dict):
        quotes = payload.get("quotes", []) or []
        tokens_in = int(payload.get("tokens_in", 0) or 0)
        tokens_out = int(payload.get("tokens_out", 0) or 0)
        citations = payload.get("citations", []) or []
        try:
            cost = float(payload.get("cost", 0.0) or 0.0)
        except Exception:
            cost = 0.0
        return {
            "quotes": quotes,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "citations": citations,
            "cost": cost,
            "raw": payload,
        }

    if isinstance(payload, list):
        if all(isinstance(x, str) for x in payload):
            quotes = list(payload)
        elif all(isinstance(x, dict) for x in payload):
            for x in payload:
                q = x.get("quotes")
                if isinstance(q, list):
                    quotes.extend(q)
                c = x.get("citations")
                if isinstance(c, list):
                    citations.extend(c)
                tokens_in += int(x.get("tokens_in", 0) or 0)
                tokens_out += int(x.get("tokens_out", 0) or 0)
                try:
                    cost += float(x.get("cost", 0.0) or 0.0)
                except Exception:
                    pass
        elif all(isinstance(x, tuple) and len(x) >= 1 for x in payload):
            for t in payload:
                if len(t) >= 1 and isinstance(t[0], str):
                    quotes.append(t[0])
                if len(t) >= 2:
                    citations.append(t[1])
        return {
            "quotes": quotes,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "citations": citations,
            "cost": cost,
            "raw": payload,
        }

    return {
        "quotes": [],
        "tokens_in": 0,
        "tokens_out": 0,
        "citations": [],
        "cost": 0.0,
        "raw": payload,
    }


def execute_plan(
    idea: str,
    tasks: list[dict[str, str]],
    agents: dict[str, object] | None = None,
    *,
    project_id: str | None = None,
    save_decision_log: bool = True,
    save_evidence: bool = True,
    project_name: str | None = None,
    ui_model: str | None = None,
    cancel: CancellationToken | None = None,
    deadline_ts: float | None = None,
    run_id: str | None = None,
) -> dict[str, str]:
    """Dispatch tasks to routed agents and collect their outputs."""

    deadline = Deadline(deadline_ts)

    def _check() -> None:
        if cancel and cancel.is_set():
            raise RuntimeError("cancelled")
        if deadline and deadline.expired():
            raise TimeoutError("deadline reached")

    def _append(step: dict, *, meta: dict | None = None) -> None:
        if run_id:
            trace_writer.append_step(run_id, step, meta=meta)

    def _flush(phase: str, meta: dict) -> None:
        if run_id:
            trace_writer.flush_phase_meta(run_id, phase, meta)

    _check()

    idea_str = idea if isinstance(idea, str) else str(idea)
    project_id = project_id or _slugify(idea_str)
    project_name = project_name or project_id
    exec_tasks = list(tasks)
    if not exec_tasks:
        try:
            _append({"phase": "executor", "summary": [], "meta": {"reason": "no_executable_tasks"}})
            _flush("executor", {"routed_tasks": 0, "exec_tasks": 0, "reason": "no_executable_tasks"})
        except Exception:
            pass

        raise ValueError("No executable tasks after planning/routing")
    agents = agents or {}
    tasks = exec_tasks
    answers: dict[str, list[str]] = {}
    role_to_findings: dict[str, dict] = {}
    alias_maps: dict[str, dict[str, str]] = {}
    open_issues: list[dict[str, str]] = []
    evidence = EvidenceSet(project_id=project_id) if save_evidence else None
    collector = AgentTraceCollector(project_id=project_id)
    prompt_previews: list[str] = []
    try:
        st.session_state.setdefault("routing_report", [])
        st.session_state.setdefault("live_status", {})
    except Exception:
        pass

    def _run_task(t: dict[str, str]) -> None:
        _check()
        with with_deadline(deadline):
            role, AgentCls, model, routed = route_task(t, ui_model)
            handle = collector.start_item(routed, role, model)
        tid = routed.get("id") or f"T{handle+1:02d}"
        step_name = routed.get("title", "")
        with otel.start_span(
            "step.executor",
            attrs={"run_id": run_id, "step_id": tid, "name": step_name},
            run_id=run_id,
        ) as span:
            span.add_event("step.start", {"step_id": tid})
            collector.append_event(
                handle,
                "route",
                {"planned_role": t.get("role"), "routed_role": role, "model": model},
            )
            if save_decision_log:
                log_decision(
                    project_id,
                    "route",
                    {"planned_role": t.get("role"), "title": routed.get("title", "")},
                )
            agent = agents.get(role)
            if agent is None:
                agent = AgentCls(model)
                agents[role] = agent
            preview = f"{routed.get('title', '')}: {routed.get('description', '')}"
            prompt_previews.append(preview[:4000])
            collector.append_event(handle, "call", {"attempt": 1})
            redactor = _get_redactor()
            if role == "Dynamic Specialist":
                brief = f"{routed.get('title', '')}: {routed.get('description', '')}"
                rb, _, _ = redactor.redact(brief, mode="light", role=role)
                spec = {
                    "role_name": role,
                    "task_brief": rb,
                    "io_schema_ref": routed.get("io_schema_ref")
                    or "dr_rd/schemas/generic_v1.json",
                    "context": {"run_id": run_id, "deadline_ts": deadline_ts},
                }
                routed["alias_map"] = dict(redactor.alias_map)
                call_task = spec
                meta_ctx = spec.get("context")
            else:
                pseudo = {
                    **routed,
                    "idea": idea_str,
                    "requirements": routed.get("requirements", []),
                    "tests": routed.get("tests", []),
                    "defects": routed.get("defects", []),
                    "context": {"run_id": run_id, "deadline_ts": deadline_ts},
                }
                for k, v in list(pseudo.items()):
                    if isinstance(v, str) and k != "role":
                        rv, _, _ = redactor.redact(v, mode="light", role=role)
                        pseudo[k] = rv
                routed["alias_map"] = dict(redactor.alias_map)
                call_task = pseudo
                meta_ctx = pseudo.get("context")
            _append({
                "phase": "executor",
                "event": "agent_start",
                "role": role,
                "task_id": routed.get("id"),
            })
            try:
                out = invoke_agent_safely(
                    agent,
                    task=call_task,
                    model=model,
                    meta=meta_ctx,
                    run_id=run_id,
                )
            except (EmptyModelOutput, JSONDecodeError) as e:
                span.set_attribute("status", "error")
                span.record_exception(e)
                safe_exc(logger, idea, f"invoke_agent[{role}]", e)
                _append({
                    "phase": "executor",
                    "event": "agent_end",
                    "role": role,
                    "task_id": routed.get("id"),
                    "ok": False,
                    "error": str(e),
                })
                err = getattr(
                    e,
                    "payload",
                    {
                        "role": role,
                        "task": routed.get("title", ""),
                        "error": str(e),
                        "raw_head": getattr(e, "raw_head", ""),
                    },
                )
                answers[role] = [
                    err if isinstance(err, str) else json.dumps(err, ensure_ascii=False)
                ]
                role_to_findings[role] = err
                alias_maps[role] = routed.get("alias_map", {})
                collector.finalize_item(handle, "", err, 0, 0, 0.0, [], [])
                return
            except Exception as e:
                span.set_attribute("status", "error")
                span.record_exception(e)
                safe_exc(logger, idea, f"invoke_agent[{role}]", e)
                _append({
                    "phase": "executor",
                    "event": "agent_error",
                    "role": role,
                    "task_id": routed.get("id"),
                    "error": str(e),
                })
                raise RuntimeError(f"agent {role} failed") from e
            _append({
                "phase": "executor",
                "event": "agent_end",
                "role": role,
                "task_id": routed.get("id"),
                "ok": True,
            })
            _check()
            text = out

            def _retry_fn(rem: str) -> str:
                collector.append_event(handle, "retry", {"attempt": 2})
                collector.append_event(handle, "call", {"attempt": 2})
                if role == "Dynamic Specialist":
                    brief = (
                        f"{routed.get('title', '')}: {routed.get('description', '')}\n{rem}"
                    ).strip()
                    rb, _, _ = redactor.redact(brief, mode="light", role=role)
                    spec_r = {
                        "role_name": role,
                        "task_brief": rb,
                        "io_schema_ref": routed.get("io_schema_ref")
                        or "dr_rd/schemas/generic_v1.json",
                        "context": {"run_id": run_id, "deadline_ts": deadline_ts},
                    }
                    routed["alias_map"] = dict(redactor.alias_map)
                    _append({
                        "phase": "executor",
                        "event": "agent_start",
                        "role": role,
                        "task_id": routed.get("id"),
                    })
                    try:
                        result = invoke_agent_safely(
                            agent,
                            task=spec_r,
                            model=model,
                            meta=spec_r.get("context"),
                            run_id=run_id,
                        )
                    except Exception as e:
                        _append(
                            {
                                "phase": "executor",
                                "event": "agent_end",
                                "role": role,
                                "task_id": routed.get("id"),
                                "ok": False,
                                "error": str(e),
                            }
                        )
                        raise RuntimeError(f"agent {role} failed") from e
                    _append(
                        {
                            "phase": "executor",
                            "event": "agent_end",
                            "role": role,
                            "task_id": routed.get("id"),
                            "ok": True,
                        }
                    )
                    return result
                retry_task = dict(routed)
                retry_task["description"] = (routed.get("description", "") + "\n" + rem).strip()
                pseudo_r = {
                    **retry_task,
                    "idea": idea_str,
                    "requirements": retry_task.get("requirements", []),
                    "tests": retry_task.get("tests", []),
                    "defects": retry_task.get("defects", []),
                    "context": {"run_id": run_id, "deadline_ts": deadline_ts},
                }
                pseudo_r, alias_map2 = pseudonymize_for_model(pseudo_r)
                retry_task["alias_map"] = alias_map2
                _append({
                    "phase": "executor",
                    "event": "agent_start",
                    "role": role,
                    "task_id": retry_task.get("id"),
                })
                try:
                    result = invoke_agent_safely(
                        agent,
                        task=pseudo_r,
                        model=model,
                        meta={"context": pseudo_r.get("context")},
                        run_id=run_id,
                    )
                except Exception as e:
                    _append({
                        "phase": "executor",
                        "event": "agent_end",
                        "role": role,
                        "task_id": retry_task.get("id"),
                        "ok": False,
                        "error": str(e),
                    })
                    raise RuntimeError(f"agent {role} failed") from e
                _append({
                    "phase": "executor",
                    "event": "agent_end",
                    "role": role,
                    "task_id": retry_task.get("id"),
                    "ok": True,
                })
                routed["alias_map"] = retry_task.get("alias_map", {})
                return result

            high_model = select_model("agent_high", agent_name=role)

            def _retry_high(rem: str) -> str:
                collector.append_event(handle, "retry", {"attempt": 3})
                collector.append_event(handle, "call", {"attempt": 3})
                if role == "Dynamic Specialist":
                    brief = (
                        f"{routed.get('title', '')}: {routed.get('description', '')}\n{rem}"
                    ).strip()
                    rb, _, _ = redactor.redact(brief, mode="light", role=role)
                    spec_r = {
                        "role_name": role,
                        "task_brief": rb,
                        "io_schema_ref": routed.get("io_schema_ref")
                        or "dr_rd/schemas/generic_v1.json",
                        "context": {"run_id": run_id, "deadline_ts": deadline_ts},
                    }
                    routed["alias_map"] = dict(redactor.alias_map)
                    _append({
                        "phase": "executor",
                        "event": "agent_start",
                        "role": role,
                        "task_id": routed.get("id"),
                    })
                    try:
                        result = invoke_agent_safely(
                            agent,
                            task=spec_r,
                            model=high_model,
                            meta=spec_r.get("context"),
                            run_id=run_id,
                        )
                    except Exception as e:
                        _append(
                            {
                                "phase": "executor",
                                "event": "agent_end",
                                "role": role,
                                "task_id": routed.get("id"),
                                "ok": False,
                                "error": str(e),
                            }
                        )
                        raise RuntimeError(f"agent {role} failed") from e
                    _append(
                        {
                            "phase": "executor",
                            "event": "agent_end",
                            "role": role,
                            "task_id": routed.get("id"),
                            "ok": True,
                        }
                    )
                    return result
                retry_task = dict(routed)
                retry_task["description"] = (
                    routed.get("description", "") + "\n" + rem
                ).strip()
                pseudo_r = {
                    **retry_task,
                    "idea": idea_str,
                    "requirements": retry_task.get("requirements", []),
                    "tests": retry_task.get("tests", []),
                    "defects": retry_task.get("defects", []),
                    "context": {"run_id": run_id, "deadline_ts": deadline_ts},
                }
                pseudo_r, alias_map2 = pseudonymize_for_model(pseudo_r)
                retry_task["alias_map"] = alias_map2
                _append({
                    "phase": "executor",
                    "event": "agent_start",
                    "role": role,
                    "task_id": retry_task.get("id"),
                })
                try:
                    result = invoke_agent_safely(
                        agent,
                        task=pseudo_r,
                        model=high_model,
                        meta={"context": pseudo_r.get("context")},
                        run_id=run_id,
                    )
                except Exception as e:
                    _append(
                        {
                            "phase": "executor",
                            "event": "agent_end",
                            "role": role,
                            "task_id": retry_task.get("id"),
                            "ok": False,
                            "error": str(e),
                        }
                    )
                    raise RuntimeError(f"agent {role} failed") from e
                _append(
                    {
                        "phase": "executor",
                        "event": "agent_end",
                        "role": role,
                        "task_id": retry_task.get("id"),
                        "ok": True,
                    }
                )
                routed["alias_map"] = retry_task.get("alias_map", {})
                return result

            _check()
            text, meta = validate_and_retry(
                role,
                routed,
                text,
                _retry_fn,
                escalate_fn=_retry_high,
                run_id=run_id,
                support_id=routed.get("support_id"),
            )
            collector.append_event(
                handle,
                "validate",
                {"retry": bool(meta.get("retried")), "escalated": meta.get("escalated")},
            )
            answers.setdefault(role, []).append(
                text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
            )
            alias_maps[role] = routed.get("alias_map", {})
            obj = text if isinstance(text, (dict, list)) else extract_json_block(text)
            payload = obj or {}
            role_to_findings[role] = payload
            norm = _normalize_evidence_payload(payload)
            finding_text = ""
            if isinstance(payload, dict):
                finding_text = str(payload.get("findings") or "")
            if not finding_text:
                finding_text = (
                    text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
                )
            finding_snip = finding_text.strip()[:240]
            is_placeholder = False
            if isinstance(payload, dict):
                is_placeholder = all(
                    payload.get(k) == "TODO" for k in ("findings", "risks", "next_steps")
                )
            if not meta.get("valid_json") or is_placeholder:
                open_issues.append(
                    {
                        "title": routed.get("title", ""),
                        "role": role,
                        "task_id": routed.get("id"),
                        "result": payload,
                    }
                )
            if evidence is not None:
                evidence.add(
                    role=role,
                    task_title=routed.get("title", ""),
                    quotes=norm.get("quotes", []),
                    tokens_in=norm.get("tokens_in", 0),
                    tokens_out=norm.get("tokens_out", 0),
                    citations=norm.get("citations", []),
                    cost_usd=norm.get("cost", 0.0),
                )
                collector.append_event(
                    handle,
                    "save_evidence",
                    {
                        "quotes": len(norm.get("quotes", [])),
                        "citations": len(norm.get("citations", [])),
                    },
                )
            collector.finalize_item(
                handle,
                finding_snip,
                payload if isinstance(payload, dict) else {},
                norm.get("tokens_in", 0),
                norm.get("tokens_out", 0),
                norm.get("cost", 0.0),
                norm.get("quotes", []),
                norm.get("citations", []),
            )
            try:  # optional KB persistence
                from core.reporting_bridge import kb_ingest

                kb_ingest(
                    role,
                    routed,
                    payload if isinstance(payload, dict) else {},
                    {"model": model},
                    norm.get("citations", []),
                )
            except Exception:
                pass
            if save_decision_log:
                log_decision(project_id, "agent_result", {"role": role, "has_json": bool(payload)})
            try:  # light budget telemetry
                from streamlit.runtime.scriptrunner import get_script_run_ctx

                if get_script_run_ctx() is not None:
                    tracker = st.session_state.get("cost_tracker")
                    if tracker:
                        tracker.spend += float(norm.get("cost", 0.0))
            except Exception:
                pass
            span.add_event(
                "step.end",
                {
                    "tokens_in": norm.get("tokens_in", 0),
                    "tokens_out": norm.get("tokens_out", 0),
                    "cost_usd": norm.get("cost", 0.0),
                },
            )

    norm_tasks = list(tasks)
    try:
        _flush("router", {"routed_tasks": len(norm_tasks)})
        _flush("executor", {"exec_tasks": len(norm_tasks)})
    except Exception:
        pass
    if len(norm_tasks) == 0:
        _append(
            {
                "phase": "executor",
                "summary": {},
                "routed_tasks": 0,
                "exec_tasks": 0,
                "meta": {"reason": "no_executable_tasks"},
            }
        )
        try:
            _flush("executor", {"exec_tasks": 0})
        except Exception:
            pass
        raise ValueError("No executable tasks after planning/routing")
    try:
        _append({"phase": "executor", "exec_tasks": len(norm_tasks), "summary": {}})
    except Exception:
        pass
    eval_round = 0
    evaluations: list[dict] = []
    while True:
        _check()
        if ff.PARALLEL_EXEC_ENABLED:
            from types import SimpleNamespace

            from core.engine.executor import run_tasks

            exec_tasks: list[dict[str, str]] = []
            for i, t in enumerate(norm_tasks, 1):
                tmp = dict(t)
                tmp.setdefault("id", f"T{i:02d}")
                tmp.setdefault("task", tmp.get("description", ""))
                exec_tasks.append(tmp)

            class _State:
                def __init__(self):
                    self.ws = SimpleNamespace(
                        read=lambda: {"results": {}},
                        save_result=lambda _id, _res, _score: None,
                    )

                def _execute(self, task: dict[str, str]):
                    _run_task(task)
                    return None, 0.0

            run_tasks(exec_tasks, state=_State())
        else:
            for t in norm_tasks:
                _run_task(t)
                _check()

        follow_ups: list[dict[str, str]] = []
        if ff.REFLECTION_ENABLED and role_to_findings:
            reflection_cls = AGENT_REGISTRY.get("Reflection")
            if reflection_cls:
                reflection_agent = agents.get("Reflection") or reflection_cls(
                    select_model("agent", ui_model, agent_name="Reflection")
                )
                agents["Reflection"] = reflection_agent
                ref_task = {
                    "role": "Reflection",
                    "title": "Review",
                    "description": json.dumps(role_to_findings),
                    "context": json.dumps(role_to_findings),
                }
                _append(
                    {
                        "phase": "executor",
                        "event": "agent_start",
                        "role": "Reflection",
                        "task_id": ref_task.get("id"),
                    }
                )
                try:
                    pseudo_r, _ = pseudonymize_for_model(
                        {"context": ref_task.get("context", idea), "task": ref_task}
                    )
                    ref_out = invoke_agent_safely(
                        reflection_agent,
                        pseudo_r.get("task", {}),
                        meta={"context": pseudo_r.get("context")},
                        run_id=run_id,
                    )
                    _append(
                        {
                            "phase": "executor",
                            "event": "agent_end",
                            "role": "Reflection",
                            "task_id": ref_task.get("id"),
                            "ok": True,
                        }
                    )
                except Exception as e:
                    _append(
                        {
                            "phase": "executor",
                            "event": "agent_end",
                            "role": "Reflection",
                            "task_id": ref_task.get("id"),
                            "ok": False,
                            "error": str(e),
                        }
                    )
                    safe_exc(logger, idea, "invoke_agent[Reflection]", e)
                    raise RuntimeError("Reflection agent failed") from e
                ref_text = ref_out if isinstance(ref_out, str) else json.dumps(ref_out)
                if "no further tasks" not in ref_text.lower():
                    try:
                        follow_ups = json.loads(extract_json_block(ref_text) or ref_text)
                    except Exception:
                        follow_ups = []
                    if not isinstance(follow_ups, list):
                        follow_ups = []

        for ft in follow_ups:
            if isinstance(ft, str):
                m = re.match(r"\[(?P<role>[^]]+)\]:\s*(?P<title>.*)", ft)
                role_hint = m.group("role") if m else None
                title = m.group("title") if m else ft
                task = {"role": role_hint, "title": title, "description": title}
            elif isinstance(ft, dict):
                task = ft
            else:
                continue
            _run_task(task)
            _check()

        if not ff.EVALUATION_ENABLED:
            break

        eval_cls = AGENT_REGISTRY.get("Evaluation")
        eval_agent = agents.get("Evaluation") if agents else None
        if eval_cls and eval_agent is None:
            eval_agent = eval_cls(select_model("agent", agent_name="Evaluation"))
            agents["Evaluation"] = eval_agent  # type: ignore
        elif eval_agent is None:
            eval_agent = EvaluationAgent()
        handle = collector.start_item(
            {"id": f"E{eval_round+1:02d}", "title": "Evaluation"},
            "Evaluation",
            "",
        )
        collector.append_event(handle, "call", {"attempt": 1})
        context = {
            "rag_enabled": ff.RAG_ENABLED,
            "live_search_enabled": ff.ENABLE_LIVE_SEARCH,
        }
        try:
            joined_answers = {k: "\n\n".join(v) for k, v in answers.items()}
            result = eval_agent.run(idea_str, joined_answers, role_to_findings, context=context)
        except Exception as e:
            collector.append_event(handle, "error", {"error": str(e)})
            _append(
                {
                    "phase": "executor",
                    "event": "agent_error",
                    "role": "Evaluation",
                    "task_id": "",
                    "error": str(e),
                }
            )
            raise RuntimeError("agent Evaluation failed") from e
        collector.append_event(handle, "evaluation", result.get("score", {}))
        collector.finalize_item(
            handle, "; ".join(result.get("findings", [])), result, 0, 0, 0.0, [], []
        )
        evaluations.append(result)
        if save_decision_log:
            log_decision(
                project_id,
                "evaluation",
                {
                    "scores": result.get("score"),
                    "insufficient": result.get("insufficient"),
                    "followups": len(result.get("followups", [])),
                },
            )
        if not result.get("insufficient") or eval_round >= ff.EVALUATION_MAX_ROUNDS:
            break
        followups = list(result.get("followups", []) or [])[:3]
        if not followups:
            break
        if ff.EVALUATION_HUMAN_REVIEW:
            try:
                st.session_state["pending_followups"] = followups
                st.session_state["awaiting_approval"] = True
            except Exception:
                pass
            break
        for fu in followups:
            collector.append_event(handle, "spawn_followup", fu)
        norm_tasks = followups
        eval_round += 1
        continue

    if evaluations and save_evidence:
        out_dir = os.path.join("audits", project_id)
        os.makedirs(out_dir, exist_ok=True)
        try:
            with open(os.path.join(out_dir, "evaluation.json"), "w", encoding="utf-8") as f:
                json.dump(evaluations, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    if save_evidence and evidence is not None:
        import csv

        rows = build_coverage(project_id, role_to_findings)
        out_dir = os.path.join("audits", project_id)
        os.makedirs(out_dir, exist_ok=True)
        if rows:
            fieldnames = ["project_id", "role"] + [
                k for k in rows[0].keys() if k not in ("project_id", "role")
            ]
            with open(
                os.path.join(out_dir, "coverage.csv"), "w", newline="", encoding="utf-8"
            ) as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        with open(os.path.join(out_dir, "evidence.json"), "w", encoding="utf-8") as f:
            json.dump(evidence.as_dicts(), f, ensure_ascii=False, indent=2)
        if save_decision_log:
            log_decision(project_id, "coverage_built", {"rows": len(rows)})

    try:
        enable_poc = st.session_state.get("enable_poc", False)
        test_plan = st.session_state.get("test_plan")
    except Exception:
        enable_poc = False
        test_plan = None
    if enable_poc and test_plan:
        report = run_poc(project_id, test_plan)
        try:
            st.session_state["poc_report"] = report
        except Exception:
            pass
    from orchestrators.spec_builder import assemble_from_agent_payloads
    from utils.reportgen import render, write_csv

    joined_answers = {k: "\n\n".join(v) for k, v in answers.items()}
    sdd, impl = assemble_from_agent_payloads(project_name, idea_str, joined_answers)
    out_dir = f"audits/{project_id}/build"
    os.makedirs(out_dir, exist_ok=True)
    sdd_md = render("build/SDD.md.j2", {"sdd": sdd})
    impl_md = render("build/ImplementationPlan.md.j2", {"impl": impl})
    open(f"{out_dir}/SDD.md", "w", encoding="utf-8").write(sdd_md)
    open(f"{out_dir}/ImplementationPlan.md", "w", encoding="utf-8").write(impl_md)
    write_csv(
        f"{out_dir}/bom.csv",
        [b.model_dump() for b in impl.bom],
        headers=["part_no", "desc", "qty", "unit_cost", "vendor"],
    )
    write_csv(
        f"{out_dir}/budget.csv",
        [b.model_dump() for b in impl.budget],
        headers=["phase", "cost_usd"],
    )
    os.makedirs(f"{out_dir}/interface_contracts", exist_ok=True)
    for i in sdd.interfaces:
        open(
            f"{out_dir}/interface_contracts/{i.name}.md",
            "w",
            encoding="utf-8",
        ).write(
            f"# {i.name}\n\nProducer: {i.producer}\n"
            f"Consumer: {i.consumer}\n\nContract:\n{i.contract}\n",
        )

    try:
        st.session_state["_last_prompt"] = "\n\n".join(prompt_previews)[:4000]
    except Exception:
        pass

    trace_data = collector.as_dicts()
    try:
        routing_report = st.session_state.get("routing_report", [])
        _append({"phase": "router", "summary": routing_report, "routed_tasks": len(routing_report)})
        _flush("router", {"routed_tasks": len(routing_report), "routing_report": routing_report})
    except Exception:
        pass
    try:
        st.session_state["agent_trace"] = trace_data
        run_id = st.session_state.get("run_id")
        if run_id:
            from utils.trace_export import (
                write_trace_csv,
                write_trace_json,
                write_trace_markdown,
            )

            write_trace_json(run_id, trace_data)
            write_trace_csv(run_id, trace_data)
            write_trace_markdown(run_id, trace_data)
    except Exception:
        pass
    try:
        st.session_state["alias_maps"] = alias_maps
        st.session_state["answers_raw"] = answers
        st.session_state["open_issues"] = open_issues
    except Exception:
        pass
    if norm_tasks:
        try:
            ctx = {"idea": idea_str}
            if run_id:
                ctx["run_id"] = run_id
            exec_artifacts(norm_tasks, ctx)
        except Exception:
            logger.warning("executor artifacts failed", exc_info=True)
    return {k: "\n\n".join(v) for k, v in answers.items()}


def compose_final_proposal(
    idea: str,
    answers: dict[str, str],
    *,
    cancel: CancellationToken | None = None,
    deadline_ts: float | None = None,
) -> str:
    """Combine agent outputs into a final proposal using the Synthesizer."""
    deadline = Deadline(deadline_ts)

    def _check() -> None:
        if cancel and cancel.is_set():
            raise RuntimeError("cancelled")
        if deadline and deadline.expired():
            raise TimeoutError("deadline reached")

    _check()
    # Build findings markdown excluding placeholder results
    raw = st.session_state.get("answers_raw") or {k: [v] for k, v in answers.items()}
    def _is_placeholder(txt: str) -> bool:
        try:
            obj = json.loads(txt)
            if isinstance(obj, dict):
                return all(obj.get(k) == "TODO" for k in ("findings", "risks", "next_steps"))
        except Exception:
            pass
        return txt.strip() == "TODO"

    parts: list[str] = []
    for role, outs in raw.items():
        for out in outs:
            if _is_placeholder(out):
                continue
            parts.append(f"### {role}\n{out}")
    open_issues = st.session_state.get("open_issues", [])
    if open_issues:
        parts.append("## Open Issues")
        for issue in open_issues:
            parts.append(
                f"- {issue.get('task_id','')} ({issue.get('role','')}): "
                f"{json.dumps(issue.get('result'), ensure_ascii=False)}"
            )
    findings_md = "\n".join(parts)
    alias_map: dict[str, str] = {}
    try:
        for m in st.session_state.get("alias_maps", {}).values():
            alias_map.update(m)
    except Exception:
        pass
    pseudo_payload, extra_map = pseudonymize_for_model({"idea": idea, "findings_md": findings_md})
    alias_map.update(extra_map)
    tpl = registry.get("Synthesizer")
    prompt = tpl.user_template.format(
        idea=pseudo_payload["idea"], findings_md=pseudo_payload["findings_md"]
    )
    system_prompt = tpl.system
    try:
        st.session_state["_last_prompt"] = (system_prompt + "\n" + prompt)[:4000]
    except Exception:
        pass
    with with_deadline(deadline):
        result = complete(system_prompt, prompt)
    _check()
    final_markdown = (result.content or "").strip()
    if not final_markdown:
        final_markdown = "Final report generation failed."
    if open_issues:
        issues_md = "\n".join(
            ["## Open Issues"]
            + [
                f"- {i.get('task_id','')} ({i.get('role','')}): "
                f"{json.dumps(i.get('result'), ensure_ascii=False)}"
                for i in open_issues
            ]
        )
        final_markdown = (final_markdown + "\n\n" + issues_md).strip()
    if alias_map:
        final_markdown = rehydrate_output(final_markdown, alias_map)
    run_id = st.session_state.get("run_id")
    if run_id:
        from utils.paths import write_text

        write_text(run_id, "report", "md", final_markdown)
    try:
        from core.final.composer import write_final_bundle
        from core.final.traceability import build_rows

        slug = st.session_state.get("project_slug", _slugify(idea))
        project_id = slug
        tasks = st.session_state.get("plan_tasks") or []
        artifacts = {
            "evidence": f"audits/{slug}/evidence.json",
            "coverage": f"audits/{slug}/coverage.csv",
            "decision_log": f"memory/decision_log/{slug}.jsonl",
            "poc_report": f"audits/{slug}/poc/results.json",
            "sdd": f"audits/{slug}/build/SDD.md",
            "impl_plan": f"audits/{slug}/build/ImplementationPlan.md",
            "bom": f"audits/{slug}/build/bom.csv",
            "budget": f"audits/{slug}/build/budget.csv",
        }
        appendices = {k: v for k, v in artifacts.items() if v and os.path.exists(v)}
        trace_rows = build_rows(
            project_id,
            st.session_state.get("intake", {}),
            tasks,
            st.session_state.get("routing_report", []),
            answers,
            appendices,
        )
        out_paths = write_final_bundle(slug, final_markdown, appendices, trace_rows)
        st.session_state["final_paths"] = out_paths
    except Exception as e:  # pragma: no cover - best effort
        logger.warning("Failed to build final bundle: %s", e)
    _check()
    return final_markdown


# Backwards compatibility
compile_proposal = compose_final_proposal


def run_poc(project_id: str, test_plan):
    """Execute Proof-of-Concept tests defined in ``test_plan``."""
    import csv
    import json
    from pathlib import Path

    from core.poc import gates
    from core.poc.results import PoCReport, TestResult
    from core.poc.testplan import TestPlan
    from memory.memory_manager import MemoryManager
    from simulation import (
        runner,
        simulation_manager,  # noqa: F401 - ensure registry hooks
    )

    if not isinstance(test_plan, TestPlan):
        test_plan = TestPlan.parse_obj(test_plan)
    results = []
    total_cost = 0.0
    total_seconds = 0.0
    for test in test_plan.tests:
        gates.assert_safe(test)
        sim_name = test.inputs.get("_sim", "thermal_mock")
        obs, meta = runner.run_sim(sim_name, test.inputs)
        total_cost += float(meta.get("cost_estimate_usd", 0.0))
        total_seconds += float(meta.get("seconds", 0.0))
        metrics_passfail = {}
        for m in test.metrics:
            val = obs.get(m.name)
            passed = False
            if val is not None:
                if m.operator == ">=":
                    passed = val >= m.target
                elif m.operator == "<=":
                    passed = val <= m.target
                elif m.operator == ">":
                    passed = val > m.target
                elif m.operator == "<":
                    passed = val < m.target
                else:
                    passed = val == m.target
            metrics_passfail[m.name] = passed
        passed = all(metrics_passfail.values())
        results.append(
            TestResult(
                test_id=test.id,
                passed=passed,
                metrics_observed=obs,
                metrics_passfail=metrics_passfail,
                notes="",
            )
        )
        if test_plan.stop_on_fail and not passed:
            break
    summary = f"total_cost_usd={total_cost:.2f}, total_seconds={total_seconds:.2f}"
    report = PoCReport(
        project_id=test_plan.project_id,
        hypothesis=test_plan.hypothesis,
        results=results,
        summary=summary,
    )

    mm = MemoryManager()
    mm.attach_poc(project_id, test_plan.dict(), report.dict())

    out_dir = Path("audits") / project_id / "poc"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "testplan.json", "w", encoding="utf-8") as f:
        json.dump(test_plan.dict(), f, indent=2)
    with open(out_dir / "results.json", "w", encoding="utf-8") as f:
        json.dump(report.dict(), f, indent=2)
    with open(out_dir / "results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["test_id", "passed", "metrics_observed", "metrics_passfail", "notes"]
        )
        writer.writeheader()
        for r in report.results:
            writer.writerow(r.dict())
    return report


def orchestrate(*args, resume_from: str | None = None, **kwargs):
    import logging

    logging.warning(
        "core.orchestrator.orchestrate is deprecated; using unified pipeline (planner→router→executor→synth)."
    )
    idea = args[0] if args else kwargs.get("idea", "")
    run_id = st.session_state.get("run_id") or ""
    phases = ["planner", "executor", "synth"]
    if resume_from:
        cp = checkpoints.load(resume_from)
        if not cp:
            resume_failed(resume_from, "missing_checkpoint")
            raise ResumeNotPossible(f"no checkpoint for {resume_from}")
        checkpoints.init(run_id, phases=phases)
        run_resumed(run_id, resume_from)
        start = {ph: cp["phases"].get(ph, {}).get("next_index", 0) for ph in phases}
    else:
        checkpoints.init(run_id, phases=phases)
        start = {ph: 0 for ph in phases}
    logger.info(
        "UnifiedPipeline: planner→router→executor→synth (parallel=%s, rag=%s, live=%s)",
        ff.PARALLEL_EXEC_ENABLED,
        ff.RAG_ENABLED,
        ff.ENABLE_LIVE_SEARCH,
    )
    tasks: list[dict[str, str]] = []
    empty_fields = 0
    run_ctx = {}
    if start["planner"] == 0:
        try:
            generate_plan(idea, run_ctx=run_ctx)
        except ValueError:
            pass
        tasks = st.session_state.get("plan_tasks", [])
        empty_fields = st.session_state.pop("plan_empty_fields", 0)
        checkpoints.mark_step_done(run_id, "planner", "plan")
    elif resume_from:
        # When resuming after planning, recover the plan from the prior trace
        for step in trace_writer.read_trace(resume_from):
            if step.get("phase") == "planner" and isinstance(step.get("summary"), list):
                tasks = step["summary"]
                break
        st.session_state["plan_tasks"] = list(tasks)
    tasks = st.session_state.get("plan_tasks", [])
    if not tasks:
        trace_writer.append_step(
            run_id,
            {
                "phase": "planner",
                "summary": [],
                "planned_tasks": 0,
                "normalized_tasks": 0,
                "empty_fields": empty_fields,
                "error": "planner_empty_or_invalid",
            },
        )
        try:
            trace_writer.flush_phase_meta(
                run_id,
                "planner",
                {"planned_tasks": 0, "normalized_tasks": 0, "empty_fields": empty_fields},
            )
        except Exception:
            pass
    agents = kwargs.get("agents") or {}
    if not tasks:
        from utils.paths import exists, read_text, write_text

        try:
            existing = read_text(run_id, "report", "md") if exists(run_id, "report", "md") else ""
            write_text(run_id, "report", "md", "planner_empty_or_invalid\n" + existing)
        except Exception:
            pass
        return ""
    results: dict[str, str] = {}
    if not resume_from:
        assert start["executor"] == 0, "Executor phase unexpectedly skipped"
    if start["executor"] == 0:
        tasks = st.session_state.get("plan_tasks", [])
        assert tasks, "Normalized tasks unexpectedly empty — check planner/normalizer handoff"
        results = execute_plan(idea, tasks, agents, run_id=run_id)
        checkpoints.mark_step_done(run_id, "executor", "exec")
    final = ""
    if start["synth"] == 0:
        final = compose_final_proposal(idea, results)
        checkpoints.mark_step_done(run_id, "synth", "synth")
    return final


def run_stream(
    idea: str,
    *,
    run_id: str,
    agents: dict | None = None,
    cancel: CancellationToken | None = None,
    deadline_ts: float | None = None,
):
    """Generator yielding structured events for streaming runs."""
    otel.configure()
    cancel = cancel or CancellationToken()
    redactor = Redactor()
    run_ctx = {"redactor": redactor, "alias_map": redactor.alias_map}
    try:
        from utils.session_store import get_session_id

        session_id = get_session_id()
    except Exception:
        session_id = None
    stream_started(run_id)
    with otel.start_span(
        "run",
        attrs={"run_id": run_id, "session_id": session_id},
        run_id=run_id,
    ):
        try:
            # Planner phase
            with otel.start_span("phase.planner", attrs={"run_id": run_id, "phase": "planner"}):
                yield Event("phase_start", phase="planner")
                with otel.start_span(
                    "step.planner",
                    attrs={"run_id": run_id, "step_id": "planner", "name": "plan"},
                    run_id=run_id,
                ) as span:
                    span.add_event("step.start", {"step_id": "planner"})
                    try:
                        generate_plan(idea, cancel=cancel, deadline_ts=deadline_ts, run_ctx=run_ctx)
                        tasks = st.session_state.get("plan_tasks", [])
                    except TimeoutError as exc:
                        span.set_attribute("status", "timeout")
                        span.record_exception(exc)
                        raise
                    except RuntimeError as exc:
                        span.set_attribute("status", "cancelled")
                        span.record_exception(exc)
                        raise
                    except ValueError as exc:
                        span.set_attribute("status", "error")
                        span.record_exception(exc)
                        tasks = []
                    span.add_event("step.end", {"tasks": len(tasks)})
                empty_fields = st.session_state.pop("plan_empty_fields", 0)
                raw_planned = st.session_state.pop("raw_planned_tasks", len(tasks))
                normalized_count = st.session_state.pop("normalized_tasks_count", len(tasks))
                text = json.dumps(tasks)
                res = safety_utils.check_text(text)
                meta = {}
                if res.findings:
                    meta["safety"] = asdict(res)
                    safety_flagged_step(run_id, "planner", [f.category for f in res.findings])
                step_data = {
                    "phase": "planner",
                    "summary": tasks,
                    "prompt_preview": st.session_state.pop("_last_prompt", None),
                    "planned_tasks": raw_planned,
                    "normalized_tasks": normalized_count,
                    "empty_fields": empty_fields,
                    **({"safety": asdict(res)} if res.findings else {}),
                }
                if not tasks:
                    step_data["error"] = "planner_empty_or_invalid"
                trace_writer.append_step(run_id, step_data)
                try:
                    trace_writer.flush_phase_meta(
                        run_id,
                        "planner",
                        {
                            "planned_tasks": raw_planned,
                            "normalized_tasks": normalized_count,
                            "empty_fields": empty_fields,
                        },
                    )
                except Exception:
                    pass
                yield Event("summary", phase="planner", text=text)
                meta_err = meta
                if not tasks:
                    meta_err = {"error": "planner_empty_or_invalid"}
                    from utils.paths import exists, read_text, write_text

                    try:
                        existing = (
                            read_text(run_id, "report", "md")
                            if exists(run_id, "report", "md")
                            else ""
                        )
                        write_text(
                            run_id,
                            "report",
                            "md",
                            "planner_empty_or_invalid\n" + existing,
                        )
                    except Exception:
                        pass
                yield Event("step_end", phase="planner", step_id="planner", meta=meta_err)
                yield Event(
                    "usage_delta",
                    meta={"prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0},
                )
                yield Event("phase_end", phase="planner")
                if not tasks:
                    yield Event("error", text="planner_empty_or_invalid")
                    stream_completed(run_id, "error")
                    return

            # Executor phase
            with otel.start_span("phase.executor", attrs={"run_id": run_id, "phase": "executor"}):
                yield Event("phase_start", phase="executor")
                with otel.start_span(
                    "step.executor",
                    attrs={"run_id": run_id, "step_id": "executor", "name": "execute"},
                    run_id=run_id,
                ) as span:
                    span.add_event("step.start", {"step_id": "executor"})
                    tasks = st.session_state.get("plan_tasks", [])
                    logger.info(
                        "Planner counters: planned=%d normalized=%d", raw_planned, normalized_count
                    )
                    logger.info("Executor starting with tasks=%d", len(tasks))
                    assert (
                        tasks
                    ), "Normalized tasks unexpectedly empty — check planner/normalizer handoff"
                    try:
                        answers = execute_plan(
                            idea,
                            tasks,
                            agents=agents or {},
                            cancel=cancel,
                            deadline_ts=deadline_ts,
                            run_id=run_id,
                        )
                    except TimeoutError as exc:
                        span.set_attribute("status", "timeout")
                        span.record_exception(exc)
                        raise
                    except RuntimeError as exc:
                        span.set_attribute("status", "cancelled")
                        span.record_exception(exc)
                        raise
                    except ValueError as exc:
                        span.set_attribute("status", "error")
                        span.record_exception(exc)
                        meta_err = {"error": "no_executable_tasks"}
                        yield Event("step_end", phase="executor", step_id="executor", meta=meta_err)
                        yield Event(
                            "usage_delta",
                            meta={"prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0},
                        )
                        yield Event("phase_end", phase="executor")
                        yield Event("error", text="no_executable_tasks")
                        stream_completed(run_id, "error")
                        return
                    span.add_event("step.end", {"tasks": len(answers)})
                text = json.dumps(answers)
                res = safety_utils.check_text(text)
                meta = {}
                if res.findings:
                    meta["safety"] = asdict(res)
                    safety_flagged_step(run_id, "executor", [f.category for f in res.findings])
                step_data = {
                    "phase": "executor",
                    "summary": answers,
                    "prompt_preview": st.session_state.pop("_last_prompt", None),
                    "routed_tasks": len(tasks),
                    "exec_tasks": len(answers),
                    **({"safety": asdict(res)} if res.findings else {}),
                }
                trace_writer.append_step(run_id, step_data)
                try:
                    trace_writer.flush_phase_meta(
                        run_id,
                        "executor",
                        {"routed_tasks": len(tasks), "exec_tasks": len(answers)},
                    )
                except Exception:
                    pass
                yield Event("summary", phase="executor", text=text)
                yield Event("step_end", phase="executor", step_id="executor", meta=meta)
                yield Event(
                    "usage_delta",
                    meta={"prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0},
                )
                yield Event("phase_end", phase="executor")

            # Synth phase
            with otel.start_span("phase.synth", attrs={"run_id": run_id, "phase": "synth"}):
                yield Event("phase_start", phase="synth")
                with otel.start_span(
                    "step.synth",
                    attrs={"run_id": run_id, "step_id": "synth", "name": "synth"},
                    run_id=run_id,
                ) as span:
                    span.add_event("step.start", {"step_id": "synth"})
                    try:
                        final = compose_final_proposal(
                            idea,
                            answers,
                            cancel=cancel,
                            deadline_ts=deadline_ts,
                        )
                    except TimeoutError as exc:
                        span.set_attribute("status", "timeout")
                        span.record_exception(exc)
                        raise
                    except RuntimeError as exc:
                        span.set_attribute("status", "cancelled")
                        span.record_exception(exc)
                        raise
                    span.add_event("step.end", {})
                res = safety_utils.check_text(final)
                meta = {}
                if res.findings:
                    meta["safety"] = asdict(res)
                    safety_flagged_step(run_id, "synth", [f.category for f in res.findings])
                trace_writer.append_step(
                    run_id,
                    {
                        "phase": "synth",
                        "summary": final,
                        "prompt_preview": st.session_state.pop("_last_prompt", None),
                        **({"safety": asdict(res)} if res.findings else {}),
                    },
                )
                yield Event("summary", phase="synth", text=final)
                yield Event("step_end", phase="synth", step_id="synth", meta=meta)
                yield Event(
                    "usage_delta",
                    meta={"prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0},
                )
                yield Event("phase_end", phase="synth")

            yield Event("done")
            stream_completed(run_id, "done")
        except Exception as exc:  # pragma: no cover - best effort
            yield Event("error", text=str(exc))
            stream_completed(run_id, "error")


def run_pipeline(idea: str, **kwargs):
    import logging

    logging.warning(
        "core.orchestrator.run_pipeline is deprecated; using unified pipeline."
    )
    run_ctx = {}
    generate_plan(idea, run_ctx=run_ctx)
    tasks = st.session_state.get("plan_tasks", [])
    agents = kwargs.get("agents") or {}
    assert tasks, "Normalized tasks unexpectedly empty — check planner/normalizer handoff"
    answers = execute_plan(idea, tasks, agents)
    final = compose_final_proposal(idea, answers)
    return final, answers, []
