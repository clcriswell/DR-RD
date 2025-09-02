import json
import os
import re
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

import config.feature_flags as ff
from core.agents.evaluation_agent import EvaluationAgent
from core.agents.unified_registry import AGENT_REGISTRY
from core.evaluation.self_check import validate_and_retry
from core.llm import complete, select_model
from core.llm_client import responses_json_schema_for
from core.observability import (
    AgentTraceCollector,
    EvidenceSet,
    build_coverage,
)
from core.plan_utils import normalize_plan_to_tasks, normalize_tasks
from core.privacy import pseudonymize_for_model, rehydrate_output
from core.router import route_task
from core.schemas import Plan, ScopeNote
from memory.decision_log import log_decision
from planning.segmenter import load_redaction_policy, redact_text
from prompts.prompts import (
    PLANNER_USER_PROMPT_TEMPLATE,
    SYNTHESIZER_TEMPLATE,
)
from utils import checkpoints, otel, trace_writer
from utils import safety as safety_utils
from utils.agent_json import extract_json_block, extract_json_strict
from utils.cancellation import CancellationToken
from utils.logging import logger, safe_exc
from utils.stream_events import Event
from utils.telemetry import (
    resume_failed,
    run_resumed,
    safety_flagged_step,
    stream_completed,
    stream_started,
)
from utils.timeouts import Deadline, with_deadline

evidence: EvidenceSet | None = None


class ResumeNotPossible(Exception):
    pass


def _invoke_agent(agent, idea: str, task: Dict[str, str], model: str | None = None) -> str:
    """Call an agent with best-effort interface detection."""

    text = f"{task.get('title', '')}: {task.get('description', '')}"
    # Preferred call signatures
    for name in ("run", "act", "execute", "__call__"):
        fn = getattr(agent, name, None)
        if callable(fn):
            try:
                return fn(idea, task, model=model)
            except TypeError:
                try:
                    return fn(idea, task)
                except TypeError:
                    try:
                        return fn(text)
                    except TypeError:
                        continue
    raise AttributeError(f"{agent.__class__.__name__} has no callable interface")


def _normalize_plan_payload(data: dict) -> dict:
    """Inject sequential task IDs and backfill missing fields."""
    if isinstance(data, dict) and isinstance(data.get("tasks"), list):
        missing = 0
        for i, t in enumerate(data["tasks"], 1):
            if not t.get("id"):
                t["id"] = f"T{i:02d}"
                missing += 1

            if "title" not in t:
                for key in ("role", "name"):
                    if t.get(key):
                        t["title"] = t[key]
                        break
            if "summary" not in t:
                for key in ("objective", "description"):
                    if t.get(key):
                        t["summary"] = t[key]
                        break
            t.setdefault("summary", "")

            for key in ("role", "name", "objective", "description"):
                t.pop(key, None)

        if missing:
            logger.info("Planner normalizer injected %d task IDs", missing)
    return data


def generate_plan(
    idea: str,
    constraints: str | None = None,
    risk_posture: str | None = None,
    ui_model: str | None = None,
    *,
    cancel: CancellationToken | None = None,
    deadline_ts: float | None = None,
) -> List[Dict[str, str]]:
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

    policy = load_redaction_policy()
    constraint_list = [c.strip() for c in (constraints or "").splitlines() if c.strip()]
    redacted_idea = redact_text(policy, idea)
    redacted_constraints = [redact_text(policy, c) for c in constraint_list]

    pseudo_flag = os.getenv("DRRD_PSEUDONYMIZE_TO_MODEL", "").lower() in ("1", "true", "yes")
    alias_map: dict[str, str] = {}
    if pseudo_flag:
        pseudo_payload, alias_map = pseudonymize_for_model(
            {"idea": redacted_idea, "constraints": redacted_constraints}
        )
        redacted_idea = pseudo_payload["idea"]
        redacted_constraints = pseudo_payload["constraints"]

    sn = ScopeNote(
        idea=redacted_idea,
        constraints=redacted_constraints,
        risk_posture=(risk_posture or "medium").lower(),
        redaction_rules=list(policy.keys()),
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

    def _call(extra: str = "") -> List[Dict[str, str]]:
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
        data = extract_json_strict(raw)
        if alias_map:
            data = rehydrate_output(data, alias_map)
        try:
            plan = Plan.model_validate(data)
        except Exception as e:
            from pydantic import ValidationError

            if isinstance(e, ValidationError):
                errors = len(e.errors())
                data = _normalize_plan_payload(data)
                try:
                    plan = Plan.model_validate(data)
                except ValidationError as e2:
                    dump_dir = Path("debug/logs")
                    dump_dir.mkdir(parents=True, exist_ok=True)
                    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S%f")
                    dump_path = dump_dir / f"planner_payload_{ts}.json"
                    dump_path.write_text(json.dumps(data, indent=2))
                    logger.error(
                        "planner.validation_failed",
                        extra={"errors": errors, "dump_path": str(dump_path)},
                    )
                    raise ValueError(
                        f"Planner JSON validation failed; payload dumped to {dump_path.name}"
                    ) from e2
            else:
                raise
        return normalize_tasks(normalize_plan_to_tasks(plan.model_dump()["tasks"]))

    system_prompt = st.session_state.get("prompt_texts", {}).get("planner", "You are the Planner.")
    if pseudo_flag:
        system_prompt += "\nPlaceholders like [PERSON_1], [ORG_1] are entity aliases. Use them verbatim. Do not invent values."

    user_prompt = PLANNER_USER_PROMPT_TEMPLATE.format(
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


def _normalize_evidence_payload(payload: Any) -> Dict[str, Any]:
    """Normalize evidence payloads of various shapes into a dict.

    Accepts dict, list[dict], list[tuple], or list[str]. Always returns a dict
    with keys: ``quotes``, ``tokens_in``, ``tokens_out``, ``citations``, ``cost``,
    and ``raw``.
    """

    quotes: List[Any] = []
    tokens_in = 0
    tokens_out = 0
    citations: List[Any] = []
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
    tasks: List[Dict[str, str]],
    agents: Dict[str, object] | None = None,
    *,
    project_id: Optional[str] = None,
    save_decision_log: bool = True,
    save_evidence: bool = True,
    project_name: Optional[str] = None,
    ui_model: str | None = None,
    cancel: CancellationToken | None = None,
    deadline_ts: float | None = None,
    run_id: str | None = None,
) -> Dict[str, str]:
    """Dispatch tasks to routed agents and collect their outputs."""

    deadline = Deadline(deadline_ts)

    def _check() -> None:
        if cancel and cancel.is_set():
            raise RuntimeError("cancelled")
        if deadline and deadline.expired():
            raise TimeoutError("deadline reached")

    _check()

    project_id = project_id or _slugify(idea)
    project_name = project_name or project_id
    agents = agents or {}
    answers: Dict[str, str] = {}
    role_to_findings: Dict[str, dict] = {}
    evidence = EvidenceSet(project_id=project_id) if save_evidence else None
    collector = AgentTraceCollector(project_id=project_id)
    prompt_previews: list[str] = []
    try:
        st.session_state.setdefault("routing_report", [])
        st.session_state.setdefault("live_status", {})
    except Exception:
        pass

    def _run_task(t: Dict[str, str]) -> None:
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
            try:
                st.session_state["routing_report"].append(
                    {
                        "task_id": tid,
                        "planned_role": t.get("role"),
                        "routed_role": role,
                        "model": model,
                    }
                )
                st.session_state["live_status"][tid] = {
                    "done": False,
                    "progress": 0.0,
                    "tokens_in": 0,
                    "tokens_out": 0,
                    "cost_usd": 0.0,
                    "model": model,
                    "role": role,
                    "title": routed.get("title", ""),
                }
            except Exception:
                pass
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
            try:
                out = _invoke_agent(agent, idea, routed, model=model)
            except Exception as e:
                span.set_attribute("status", "error")
                span.record_exception(e)
                safe_exc(logger, idea, f"invoke_agent[{role}]", e)
                out = "out"
            _check()
            text = out if isinstance(out, str) else json.dumps(out)

            def _retry_fn(rem: str) -> str:
                collector.append_event(handle, "retry", {"attempt": 2})
                collector.append_event(handle, "call", {"attempt": 2})
                retry_task = dict(routed)
                retry_task["description"] = (routed.get("description", "") + "\n" + rem).strip()
                return _invoke_agent(agent, idea, retry_task, model=model)

            _check()
            text, meta = validate_and_retry(role, routed, text, _retry_fn)
            collector.append_event(handle, "validate", {"retry": bool(meta.get("retried"))})
            answers[role] = answers.get(role, "") + ("\n\n" if role in answers else "") + text
            payload = extract_json_block(text) or {}
            role_to_findings[role] = payload
            norm = _normalize_evidence_payload(payload)
            finding_text = ""
            if isinstance(payload, dict):
                finding_text = str(payload.get("findings") or "")
            if not finding_text:
                finding_text = text
            finding_snip = finding_text.strip()[:240]
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
            try:
                st.session_state["live_status"][tid] = {
                    "done": True,
                    "progress": 1.0,
                    "tokens_in": norm.get("tokens_in", 0),
                    "tokens_out": norm.get("tokens_out", 0),
                    "cost_usd": norm.get("cost", 0.0),
                    "model": model,
                    "role": role,
                    "title": routed.get("title", ""),
                }
            except Exception:
                pass
            if save_decision_log:
                log_decision(project_id, "agent_result", {"role": role, "has_json": bool(payload)})
            try:  # light budget telemetry
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

    norm_tasks = list(normalize_tasks(tasks))
    eval_round = 0
    evaluations: List[dict] = []
    while True:
        _check()
        if ff.PARALLEL_EXEC_ENABLED:
            from types import SimpleNamespace

            from core.engine.executor import run_tasks

            exec_tasks: List[Dict[str, str]] = []
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

                def _execute(self, task: Dict[str, str]):
                    _run_task(task)
                    return None, 0.0

            run_tasks(exec_tasks, max_workers=min(4, len(exec_tasks)), state=_State())
        else:
            for t in norm_tasks:
                _run_task(t)
                _check()

        follow_ups: List[Dict[str, str]] = []
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
                }
                try:
                    ref_out = _invoke_agent(reflection_agent, idea, ref_task)
                except Exception as e:
                    safe_exc(logger, idea, "invoke_agent[Reflection]", e)
                    ref_out = "no further tasks"
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
        result = eval_agent.run(idea, answers, role_to_findings, context=context)
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
    enable_build = os.environ.get("DRRD_ENABLE_BUILD_SPEC", "false").lower() == "true"
    if enable_build:
        from orchestrators.spec_builder import assemble_from_agent_payloads
        from utils.reportgen import render, write_csv

        sdd, impl = assemble_from_agent_payloads(project_name, idea, answers)
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
                f"Consumer: {i.consumer}\n\nContract:\n{i.contract}\n"
            )

    try:
        st.session_state["_last_prompt"] = "\n\n".join(prompt_previews)[:4000]
    except Exception:
        pass

    trace_data = collector.as_dicts()
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
    return answers


def compose_final_proposal(
    idea: str,
    answers: Dict[str, str],
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
    findings_md = "\n".join(f"### {r}\n{a}" for r, a in answers.items())
    prompt = SYNTHESIZER_TEMPLATE.format(idea=idea, findings_md=findings_md)
    system_prompt = st.session_state.get("prompt_texts", {}).get(
        "synthesizer", "You are an expert R&D writer."
    )
    try:
        st.session_state["_last_prompt"] = (system_prompt + "\n" + prompt)[:4000]
    except Exception:
        pass
    with with_deadline(deadline):
        result = complete(system_prompt, prompt)
    _check()
    final_markdown = (result.content or "").strip()
    run_id = st.session_state.get("run_id")
    if run_id:
        from utils.paths import write_text

        write_text(run_id, "report", "md", final_markdown)
    try:
        from core.final.composer import write_final_bundle
        from core.final.traceability import build_rows

        slug = st.session_state.get("project_slug", _slugify(idea))
        project_id = slug
        tasks = st.session_state.get("plan_tasks") or st.session_state.get("plan") or []
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
    tasks: List[Dict[str, str]] = []
    if start["planner"] == 0:
        tasks = generate_plan(idea)
        checkpoints.mark_step_done(run_id, "planner", "plan")
    agents = kwargs.get("agents") or {}
    results: Dict[str, str] = {}
    if start["executor"] == 0:
        results = execute_plan(idea, tasks, agents)
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
    **kwargs,
):
    """Generator yielding structured events for streaming runs."""
    otel.configure()
    cancel = cancel or CancellationToken()
    try:
        from utils.session_store import get_session_id

        session_id = get_session_id()
    except Exception:
        session_id = None
    mode = kwargs.get("mode") or st.session_state.get("mode")
    prompt_texts = kwargs.get("prompt_texts") or {}
    prompt_pins = kwargs.get("prompt_pins") or {}
    try:
        st.session_state.setdefault("prompt_texts", {}).update(prompt_texts)
        st.session_state.setdefault("prompt_pins", {}).update(prompt_pins)
    except Exception:
        pass
    stream_started(run_id)
    with otel.start_span(
        "run",
        attrs={"run_id": run_id, "mode": mode, "session_id": session_id},
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
                        tasks = generate_plan(idea, cancel=cancel, deadline_ts=deadline_ts)
                    except TimeoutError as exc:
                        span.set_attribute("status", "timeout")
                        span.record_exception(exc)
                        raise
                    except RuntimeError as exc:
                        span.set_attribute("status", "cancelled")
                        span.record_exception(exc)
                        raise
                    span.add_event("step.end", {"tasks": len(tasks)})
                text = json.dumps(tasks)
                res = safety_utils.check_text(text)
                meta = {}
                if res.findings:
                    meta["safety"] = asdict(res)
                    safety_flagged_step(run_id, "planner", [f.category for f in res.findings])
                trace_writer.append_step(
                    run_id,
                    {
                        "phase": "planner",
                        "summary": tasks,
                        "prompt_preview": st.session_state.pop("_last_prompt", None),
                        **({"safety": asdict(res)} if res.findings else {}),
                    },
                )
                yield Event("summary", phase="planner", text=text)
                yield Event("step_end", phase="planner", step_id="planner", meta=meta)
                yield Event(
                    "usage_delta",
                    meta={"prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0},
                )
                yield Event("phase_end", phase="planner")

            # Executor phase
            with otel.start_span("phase.executor", attrs={"run_id": run_id, "phase": "executor"}):
                yield Event("phase_start", phase="executor")
                with otel.start_span(
                    "step.executor",
                    attrs={"run_id": run_id, "step_id": "executor", "name": "execute"},
                    run_id=run_id,
                ) as span:
                    span.add_event("step.start", {"step_id": "executor"})
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
                    span.add_event("step.end", {"tasks": len(answers)})
                text = json.dumps(answers)
                res = safety_utils.check_text(text)
                meta = {}
                if res.findings:
                    meta["safety"] = asdict(res)
                    safety_flagged_step(run_id, "executor", [f.category for f in res.findings])
                trace_writer.append_step(
                    run_id,
                    {
                        "phase": "executor",
                        "summary": answers,
                        "prompt_preview": st.session_state.pop("_last_prompt", None),
                        **({"safety": asdict(res)} if res.findings else {}),
                    },
                )
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


def run_pipeline(idea: str, mode: str = "test", **kwargs):
    import logging

    logging.warning(
        "core.orchestrator.run_pipeline is deprecated; mode parameter ignored; using unified pipeline."
    )
    tasks = generate_plan(idea)
    agents = kwargs.get("agents") or {}
    answers = execute_plan(idea, tasks, agents)
    final = compose_final_proposal(idea, answers)
    return final, answers, []
