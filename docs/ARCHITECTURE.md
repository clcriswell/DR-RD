# Agents layout
- core/agents: canonical executable agents + registry used at runtime.
- agents: UI-only wrappers (PlannerAgent, SynthesizerAgent) and any view helpers.
- legacy agents directory: deprecated shim removed after migration to core.agents.

The app builds agents via core/agents/unified_registry.build_agents_unified(...). The HRM “Pro” loop runs through orchestrators/router + orchestrators/plan_utils.

## Modes and cost tracking

The system operates in two modes:

- **deep** – full reasoning with all features.
- **test** – routes every stage to a cheap model for dry runs.

Token usage is logged via a CostTracker. Costs are tracked for telemetry only; caps are not enforced.

## Sanitization

External queries follow a strict order: **redact → route → log → network**. Queries are obfuscated before any logging or network transmission.

## Intake Fields

The intake UI accepts optional **Constraints** and a **Risk posture** selection (Low/Medium/High). These values are threaded into planning prompts and persisted with each project.
