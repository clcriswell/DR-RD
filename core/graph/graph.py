from __future__ import annotations

from functools import partial
from typing import List, Optional

from .state import GraphState
from .nodes import plan_node, route_node, agent_node, tool_node, collect_node, synth_node


def run_langgraph(
    idea: str,
    constraints: Optional[List[str]] = None,
    risk_posture: Optional[str] = None,
    ui_model: Optional[str] = None,
) -> tuple[str, dict, dict]:
    """Execute the LangGraph orchestration pipeline.

    Returns
    -------
    tuple
        (final_markdown, answers, {"trace": trace, "tool_trace": tool_trace})
    """

    try:
        from langgraph.graph import END, START, StateGraph
    except Exception as e:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "LangGraph is required for graph orchestration. Install with `pip install langgraph`."
        ) from e

    import config.feature_flags as ff

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

    g = StateGraph(GraphState)
    g.add_node("plan", partial(plan_node, ui_model=ui_model))
    g.add_node("route", partial(route_node, ui_model=ui_model))
    g.add_node("agent", partial(agent_node, ui_model=ui_model))
    g.add_node("tool", tool_node)
    g.add_node("collect", collect_node)
    g.add_node("synth", partial(synth_node, ui_model=ui_model))

    g.add_edge("plan", "route")
    g.add_edge("route", "agent")
    g.add_conditional_edges(
        "agent",
        lambda s: bool(getattr(s.tasks[s.cursor], "tool_request", None)),
        {True: "tool", False: "collect"},
    )
    g.add_edge("tool", "collect")
    g.add_conditional_edges(
        "collect",
        lambda s: s.cursor < len(s.tasks),
        {True: "route", False: "synth"},
    )
    g.add_edge("synth", END)
    g.add_edge(START, "plan")

    app = g.compile()
    invoke_kwargs = {"max_steps": ff.GRAPH_MAX_STEPS}
    if ff.PARALLEL_EXEC_ENABLED:
        invoke_kwargs["parallelism"] = ff.GRAPH_PARALLELISM
    final_state = app.invoke(state, **invoke_kwargs)

    return (
        final_state.get("final", ""),
        final_state.get("answers", {}),
        {"trace": final_state.get("trace", []), "tool_trace": final_state.get("tool_trace", [])},
    )
