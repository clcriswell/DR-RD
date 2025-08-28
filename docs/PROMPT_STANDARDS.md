# Prompt Standards

## Template Fields & Versioning
- **id** and **version** identify a prompt template. Combined they form a unique key such as `planner.v1`.
- **role** and **task_key** select the template for a caller.
- **system** and **user_template** provide the base messages used by the model. `user_template` is formatted with runtime `inputs`.
- **io_schema_ref** points to a JSON schema contract the model must follow.
- **retrieval_policy** controls how aggressively the model should fetch external context.
- **evaluation_hooks**, **safety_notes**, **provider_hints**, **examples_ref** are optional metadata.

Registering a new version requires an explicit call to `PromptRegistry.register`. The latest registered version wins.

## Retrieval Policies
- `NONE`: no retrieval; `top_k=0`, no sources.
- `LIGHT`: small number of sources (`top_k=5`), conservative budget.
- `AGGRESSIVE`: broad search (`top_k=10`), generous budget.

Retrieval instructions are included only when either `config.feature_flags.RAG_ENABLED` or `ENABLE_LIVE_SEARCH` is true. The factory maps policies to `{top_k, source_types, budget_hint}` and adds citation requirements when retrieval is active.

## JSON Guardrails & Citations
All prompts remind the model:
> "You must reply only with a JSON object matching the schema: <io_schema_ref>."

When retrieval is enabled, prompts also require inline numbered citations and a final `sources` list.

## Using the PromptFactory
Agents request prompts through `PromptFactory.build_prompt` providing:
`{"role", "task", "inputs", "io_schema_ref", "retrieval_policy", ...}`.

`build_prompt` resolves a template, injects guardrails and retrieval instructions, and returns:
```
{
  "system": "...",
  "user": "...",
  "io_schema_ref": "...",
  "retrieval": {...},
  "llm_hints": {...},
  "evaluation_hooks": [...]
}
```
Future agents should reference `io_schema_ref` and use `PromptFactory` instead of hardcoded prompts.
