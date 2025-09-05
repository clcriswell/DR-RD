# Privacy Segmentation

The execution pipeline isolates context for each field. The Planner emits tasks with a
canonical `field` key (e.g. `finance`, `regulatory`) and a minimal `context`
string describing only what that field needs to know. During execution the
orchestrator:

1. selects the agent for the task,
2. aliases detected entities per field,
3. pseudonymizes the context via the central `Redactor`, and
4. dispatches the sanitized payload to the agent.

When placeholders appear in prompts, a note like "Placeholders like
`[PERSON_1]`, `[ORG_1]` are aliases. Use them verbatim." is appended to the
system prompt so downstream models preserve the tokens. The redactor maintains a
run-scoped alias map to ensure that repeated entities receive stable numbering
throughout execution.

Aliases are reversible only during final synthesis. Intermediate requests and
logs contain placeholder tokens like `[PERSON_1]`. The combined alias map is
applied after the Synthesizer runs so that the final report restores the
original entities.

## Example

A two-field plan might produce tasks:

```json
[
  {"role": "Regulatory", "field": "regulatory", "context": "Review [ORG_1] filing"},
  {"role": "Finance", "field": "finance", "context": "Model [PERSON_1] budget"}
]
```

Each agent sees only its `context` with aliased entities. The final proposal is
de-aliased before presentation.
