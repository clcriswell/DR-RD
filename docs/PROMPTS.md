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

## JSON Validation Fallback

Agents invoked through `PromptFactoryAgent` automatically retry with a
simplified prompt and a relaxed fallback schema when the initial response fails
JSON validation.  The fallback may leave non-essential fields blank or marked as
"Not determined," but a valid JSON object is always returned so downstream
orchestrators do not crash.
