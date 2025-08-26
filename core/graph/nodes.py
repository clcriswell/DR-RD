from __future__ import annotations

import json
from typing import Any

from .state import GraphState, GraphTask
from .hooks import node_start, node_end


def plan_node(state: GraphState, ui_model: str | None = None) -> GraphState:
    """Planner node: generate task list."""
    node_start(state, "plan")
    from core.orchestrator import generate_plan

    constraint_text = "\n".join(state.constraints or [])
    tasks = generate_plan(state.idea, constraint_text, state.risk_posture, ui_model=ui_model)
    state.tasks = [GraphTask(**t) for t in tasks]
    state.cursor = 0
    node_end(state, "plan")
    return state


def route_node(state: GraphState, ui_model: str | None = None) -> GraphState:
    task = state.tasks[state.cursor]
    node_start(state, "route", task.id)
    from core.router import route_task

    role, _cls, _model, routed = route_task(task.model_dump(), ui_model=ui_model)
    task.role = role
    # preserve any fields from router
    state.tasks[state.cursor] = GraphTask(**routed)
    node_end(state, "route", task.id)
    return state


def retrieval_node(state: GraphState, ui_model: str | None = None) -> GraphState:
    """Run retrieval (RAG + live search) for the current task if enabled."""

    task = state.tasks[state.cursor]
    node_start(state, "retrieval", task.id)
    from core.retrieval import query_builder, rag, live_search, normalize, provenance
    from config import feature_flags as ff

    run_retrieval = ff.RAG_ENABLED or ff.ENABLE_LIVE_SEARCH
    if not run_retrieval:
        node_end(state, "retrieval", task.id)
        return state

    queries = query_builder.build_queries(
        task.description,
        state.idea,
        state.constraints,
        state.risk_posture,
    )
    sources: list[dict] = []
    if ff.RAG_ENABLED:
        sources.extend(rag.rag_search(queries, ff.RAG_TOPK))
    if ff.ENABLE_LIVE_SEARCH:
        sources.extend(live_search.live_search(queries, {}))
    merged = normalize.merge_and_dedupe(sources)

    if task.id not in state.answers:
        state.answers[task.id] = {}
    state.answers[task.id]["retrieval_sources"] = merged
    summary_lines = [f"- {s.get('title') or s.get('url')}" for s in merged]
    state.answers[task.id]["retrieval_context"] = "\n".join(summary_lines)
    state.retrieved.setdefault(task.id, []).extend(merged)
    provenance.record_sources(task.id, merged)
    node_end(state, "retrieval", task.id)
    return state


def agent_node(state: GraphState, ui_model: str | None = None) -> GraphState:
    task = state.tasks[state.cursor]
    node_start(state, "agent", task.id)
    from core.router import dispatch

    existing = state.answers.get(task.id, {})
    task_dict = task.model_dump()
    ctx = existing.get("retrieval_context")
    if ctx:
        task_dict["context"] = ctx
    raw = dispatch(task_dict, ui_model=ui_model)
    if isinstance(raw, str):
        try:
            payload: Any = json.loads(raw)
        except Exception:
            payload = {"content": raw}
    elif isinstance(raw, dict):
        payload = raw
    else:
        payload = {"content": str(raw)}

    if isinstance(existing, dict):
        if existing.get("tool_result") and "tool_result" not in payload:
            payload["tool_result"] = existing["tool_result"]
        if existing.get("retrieval_sources") and "retrieval_sources" not in payload:
            payload["retrieval_sources"] = existing["retrieval_sources"]
        if existing.get("retrieval_context") and "retrieval_context" not in payload:
            payload["retrieval_context"] = existing["retrieval_context"]

    state.answers[task.id] = payload
    tool_req = payload.get("tool_request") if isinstance(payload, dict) else None
    if isinstance(tool_req, dict) and tool_req.get("tool") != "apply_patch":
        task.tool_request = tool_req
    node_end(state, "agent", task.id)
    return state


def tool_node(state: GraphState) -> GraphState:
    task = state.tasks[state.cursor]
    node_start(state, "tool", task.id)
    from core import tool_router

    before = list(tool_router.get_provenance())
    try:
        result = tool_router.call_tool(
            task.role or "", task.tool_request.get("tool"), task.tool_request.get("params", {})
        )
    except Exception as e:  # pylint: disable=broad-except
        result = {"error": str(e)}
    after = list(tool_router.get_provenance())
    if task.id not in state.answers:
        state.answers[task.id] = {}
    state.answers[task.id]["tool_result"] = result
    delta = after[len(before) :]
    state.tool_trace.extend(delta)
    node_end(state, "tool", task.id)
    return state


def collect_node(state: GraphState) -> GraphState:
    task = state.tasks[state.cursor]
    node_start(state, "collect", task.id)
    state.cursor += 1
    node_end(state, "collect", task.id)
    return state


def synth_node(state: GraphState, ui_model: str | None = None) -> GraphState:
    node_start(state, "synth")
    from core.orchestrator import compose_final_proposal

    result = compose_final_proposal(state.idea, state.answers)
    if isinstance(result, dict):
        state.final = result.get("document", "")
    else:
        state.final = str(result)
    node_end(state, "synth")
    return state


def attach_evaluation(state: GraphState, task_id: str, scorecard) -> None:
    """Attach ``scorecard`` under ``answers[task_id]['evaluation']``."""
    if task_id not in state.answers:
        state.answers[task_id] = {}
    state.answers[task_id]["evaluation"] = getattr(scorecard, "__dict__", scorecard)
