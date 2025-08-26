# LangGraph Orchestration

This module introduces an optional orchestration path powered by [LangGraph](https://github.com/langchain-ai/langgraph).
The graph coordinates the following nodes:

```
Planner → Router → Agent → (Tool Router) → Collector → Synthesizer
```

## State

`core/graph/state.py` defines the Pydantic models used to move data between nodes:

- **GraphTask**: `id`, `role`, `title`, `description`, optional `stop_rules` and
  `tool_request`.
- **GraphState**: top‑level idea, constraints, risk posture, a task list, cursor
  position, accumulated answers, node trace and tool‑call provenance.

## Execution Flow

1. **plan_node** – calls the existing planner to produce tasks and normalises
   them into `GraphTask` objects.
2. **route_node** – resolves the agent/model for the current task via the core
   router.
3. **agent_node** – dispatches the task to the chosen agent. If the agent emits
   a `tool_request` (e.g. `simulate`, `read_repo`, `analyze_image`), the request
   is attached to the task.
4. **tool_node** – invokes `core.tool_router.call_tool` when a task carries a
   `tool_request`. Results are stored under `answers[task_id]['tool_result']` and
   provenance deltas from `core.tool_router.get_provenance()` are appended to the
   state's `tool_trace`.
5. **collect_node** – advances the task cursor until all tasks complete, then
   branches to the synthesiser.
6. **synth_node** – composes the final proposal using the collected answers.

All node start/end events are recorded in `state.trace` via small helper hooks.

## Enabling

The graph is guarded behind the `GRAPH_ENABLED` feature flag and an optional
sidebar toggle in the Streamlit UI. The application falls back to the classic
orchestration when LangGraph is not installed.

## Provenance

Tool invocations are captured by `core.tool_router` and exposed alongside the
per‑node trace. The Streamlit UI writes the bundle to
`audits/<project_id>/graph_trace.json` and exposes a download button for manual
inspection.

## Retries & Backoff

Agent calls are wrapped with evaluator‑gated retries. Each attempt is scored
via `dr_rd.evaluation.scorecard`. If the overall score falls below
`EVALUATOR_MIN_OVERALL` the system waits using an exponential backoff schedule
and retries until the limit is reached. Attempt metadata is appended to the
graph trace.

## Evaluator Gating

Evaluators are toggled by the `EVALUATORS_ENABLED` flag. When enabled the
scorecard is attached to each task's answer under the `evaluation` key. The UI
exposes a concise row of metric scores and an expander with per‑attempt
rationales.

## Parallel Fan Out

When `PARALLEL_EXEC_ENABLED` is true the graph fans out independent tasks using
`core.graph.scheduler.ParallelLimiter`. The `max_concurrency` setting bounds the
number of simultaneous agent executions.

## AutoGen Mode

An experimental AutoGen orchestrator lives under `core.autogen.run`. Enable it
via the `AUTOGEN_ENABLED` flag and select "AutoGen" in the UI's orchestration
controls. The implementation mirrors the LangGraph tool surface but remains
sandboxed and optional.
