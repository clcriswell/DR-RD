"""LangGraph orchestration with parallel fan-out and evaluator-gated retries."""
from __future__ import annotations

from typing import List, Optional, Dict, Any
import time

import config.feature_flags as ff
from .state import GraphState, GraphTask
from .nodes import (
    plan_node,
    route_node,
    agent_node,
    tool_node,
    collect_node,
    synth_node,
    attach_evaluation,
)
from .hooks import agent_attempt
from .scheduler import ParallelLimiter, ExponentialBackoff
from dr_rd.evaluation.scorecard import evaluate


def _process_task(
    base_state: GraphState,
    task: GraphTask,
    ui_model: str | None,
    max_retries: int,
    backoff_cfg: Dict[str, float],
) -> tuple[str, Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
    state = GraphState(
        idea=base_state.idea,
        constraints=base_state.constraints,
        risk_posture=base_state.risk_posture,
        tasks=[task],
        cursor=0,
        answers={},
        trace=[],
        tool_trace=[],
    )
    backoff = ExponentialBackoff(**backoff_cfg)
    attempt = 0
    while True:
        attempt += 1
        agent_node(state, ui_model)
        payload = state.answers.get(task.id, {})
        content = payload.get("content", "")
        context = {"tool_result": payload.get("tool_result")}
        scorecard = evaluate(content, context)
        attach_evaluation(state, task.id, scorecard)
        retry = scorecard.overall < ff.EVALUATOR_MIN_OVERALL and attempt <= max_retries
        agent_attempt(state, task.id, attempt, scorecard.overall, retry)
        if not retry:
            break
        time.sleep(backoff.next())
    if task.tool_request:
        tool_node(state)
    collect_node(state)
    answer = state.answers.get(task.id, {})
    return task.id, answer, state.trace, state.tool_trace


def run_langgraph(
    idea: str,
    constraints: Optional[List[str]] = None,
    risk_posture: Optional[str] = None,
    ui_model: Optional[str] = None,
    *,
    max_concurrency: int = 1,
    max_retries: int = 0,
    retry_backoff: Optional[Dict[str, float]] = None,
    evaluators_enabled: Optional[bool] = None,
) -> tuple[str, dict, dict]:
    """Execute the LangGraph orchestration pipeline."""
    if evaluators_enabled is not None:
        ff.EVALUATORS_ENABLED = evaluators_enabled

    state = GraphState(
        idea=idea,
        constraints=constraints or [],
        risk_posture=risk_posture or "medium",
        tasks=[],
        cursor=0,
        answers={},
        trace=[],
        tool_trace=[],
    )
    plan_node(state, ui_model)
    for idx in range(len(state.tasks)):
        state.cursor = idx
        route_node(state, ui_model)

    limiter = ParallelLimiter(max_concurrency if ff.PARALLEL_EXEC_ENABLED else 1)
    backoff_cfg = retry_backoff or {}
    futures = [
        limiter.submit(
            _process_task,
            state,
            t,
            ui_model,
            max_retries,
            backoff_cfg,
        )
        for t in state.tasks
    ]

    answers: Dict[str, Any] = {}
    trace: List[Dict[str, Any]] = []
    tool_trace: List[Dict[str, Any]] = []
    for fut in futures:
        task_id, ans, tr, tt = fut.result()
        answers[task_id] = ans
        trace.extend(tr)
        tool_trace.extend(tt)

    state.answers = answers
    state.trace = trace
    state.tool_trace = tool_trace
    synth_node(state, ui_model)
    return state.final or "", answers, {"trace": trace, "tool_trace": tool_trace}
