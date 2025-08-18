# Agents layout
- core/agents: canonical executable agents + registry used at runtime.
- agents: UI-only wrappers (PlannerAgent, SynthesizerAgent) and any view helpers.
- dr_rd/agents: deprecated shim that re-exports core agents.

The app builds agents via core/agents/unified_registry.build_agents_unified(...). The HRM “Pro” loop runs through orchestrators/router + orchestrators/plan_utils.
