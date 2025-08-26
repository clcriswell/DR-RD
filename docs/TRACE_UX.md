# Agent Trace UX

The UI surfaces agent execution events from multiple sources in a unified format.

## Event Schema
Events are normalised to the following structure:

```json
{
  "ts": float,                # timestamp
  "node": str,                # graph node or component
  "phase": str,               # event type
  "task_id": str | null,
  "agent": str | null,
  "tool": str | null,
  "score": float | null,
  "attempt": int | null,
  "duration_s": float | null,
  "tokens": int | null,
  "cost_usd": float | null,
  "meta": {"...": "..."}
}
```

## Merging
`core.trace.merge.merge_traces` accepts LangGraph, tool, retrieval and optional
AutoGen traces, redacts secrets, and sorts events by timestamp. Totals can be
computed with `core.trace.merge.summarize`.

## UI Features
- Filters by task, agent and tool
- Toggle "Show retries only"
- Timestamp range slider
- Timeline table limited to `TRACE_MAX_ROWS`
- Duration line chart (`CHART_MAX_POINTS` cap)
- Per-task summary table
- Search box over node/agent/tool/meta
- Saved views (store & recall filter sets)
- Compare two saved runs side-by-side
- Export merged trace as JSON or CSV
- Export duration chart as PNG/SVG

If no trace is available for a run an informative message is shown.
