# Prompt Registry

Prompt templates are defined in code under `dr_rd/prompting/prompt_registry.py`.
Each prompt is represented by a `PromptTemplate` dataclass and registered with a
`PromptRegistry` instance. Prompts can be looked up by role at runtime:

```python
from dr_rd.prompting.prompt_registry import registry
planner = registry.get("Planner")
print(planner.system)
```

The previous YAML-based prompt files and editing utilities have been removed.
The registry is the single source of truth and prompts cannot be modified at
runtime.

## Auto-Correction and Fallback

Agents invoked through `PromptFactoryAgent` attempt to repair malformed JSON
before giving up.  Common issues like trailing commas, unquoted keys and fenced
code blocks are auto-corrected and then revalidated against the role schema. If
validation still fails, the agent retries with a simplified prompt and a
relaxed fallback schema. The fallback may leave non-essential fields blank or
marked as "Not determined," but a valid JSON object is always returned so
downstream orchestrators do not crash.

Before validation, responses pass through a `sanitize_sources` step that coerces
the `sources` field to match each role's schema. Finance and Marketing agents
must return `sources` as a list of citation strings or URLs; any objects or empty
entries are dropped. Regulatory still expects `sources` to be objects with
`id`, `title`, and optional `url` fields.

## JSON Formatting Rules

Each agent prompt explicitly defines the required `sources` type (strings or
objects with `id`, `title`, and optional `url`). Markdown links and bullet lists
are prohibited inside JSON values. If multiple items belong in a string field,
join them with semicolons in a single string.
