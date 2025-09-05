# Retry Ladder and Placeholder Behavior

Agent outputs are validated for a strict JSON contract. Validation proceeds in
two steps:

1. **Self‑check retry** – The initial response is parsed and checked for the
   required keys (`role`, `task`, `findings`, `risks`, `next_steps`,
   `sources`). If the payload is missing data, the agent is reminded with the
   same model to return the JSON object only.
2. **Escalation** – If the corrected attempt is still invalid, the orchestrator
   escalates to a stronger model profile
   (`select_model("agent_high", agent_name=role)`) and appends a concise keys
   reminder. The escalated output is validated once more.

If the escalated attempt remains invalid, a placeholder JSON object is emitted
with

```json
{
  "role": "<role>",
  "task": "<task title>",
  "findings": "TODO",
  "risks": "TODO",
  "next_steps": "TODO",
  "sources": []
}
```

Logs record when escalation starts, which model was chosen, and when a
placeholder is produced. Downstream components always receive a JSON string—
either the validated agent output or the placeholder—avoiding silent drops.

