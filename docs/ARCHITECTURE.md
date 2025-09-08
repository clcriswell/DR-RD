# Agents layout
- core/agents: canonical executable agents + registry used at runtime.
- agents: UI-only wrappers (PlannerAgent, SynthesizerAgent) and any view helpers.
- legacy agents directory: deprecated shim removed after migration to core.agents.

The app builds agents via core/agents/unified_registry.build_agents_unified(...). The orchestrator executes a single "Planner → Router/Registry → Executor → Evaluation → Synthesizer" pipeline regardless of profile. Runtime knobs are exposed as feature-flag toggles rather than separate modes. The Evaluation stage scores clarity, completeness, and grounding of agent outputs and may spawn follow‑up tasks before synthesis.

## Runtime toggles and cost tracking

Only the **Standard** profile is supported. Retrieval features (RAG and Live Search) and budgets are controlled via `config.feature_flags` and may be adjusted at runtime through `apply_overrides`.
Token usage is logged via a CostTracker for telemetry; caps may be enforced via configuration budgets.

## Sanitization

External queries follow a strict order: **redact → route → log → network**. Queries are obfuscated before any logging or network transmission.

## Intake Fields

The intake UI accepts optional **Constraints** and a **Risk posture** selection (Low/Medium/High). These values are threaded into planning prompts and persisted with each project.

## Retry and Fallback

Agents built on `PromptFactoryAgent` first attempt to auto-correct malformed JSON
responses.  Structural fixes (trailing commas, unquoted keys, etc.) are applied
before validating against the role schema.  If the response still fails
validation or required fields are missing, the agent issues a simplified
fallback prompt with a relaxed schema.  The fallback always yields a minimal but
valid JSON object so downstream stages never see `(Agent failed to return content)`.
