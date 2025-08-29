# Migration Guide: v1 Agents to PromptFactory

This guide helps contributors migrate legacy inline-prompt agents to the
`PromptRegistry`/`PromptFactory` architecture. It targets repository
maintainers using Python 3.10+ with `pip` and `pytest` available.

## Before / After

```text
Legacy inline prompt          PromptFactory + Registry
-----------------------       -------------------------
Agent -> build strings        Agent -> PromptFactory.build_prompt(spec)
             |                              |
         call model                     JSON‑strict contract
```

## Role Mapping

| Legacy role/class                          | New template id                       | Output schema                                   | Retrieval default | Tool allowlist | Evaluator hooks |
| ------------------------------------------ | ------------------------------------ | ----------------------------------------------- | ---------------- | -------------- | --------------- |
| Documentation                              | `documentation.v1`                   | `dr_rd/schemas/documentation_agent.json`         | LIGHT            | none           | `self_check_minimal` |
| Data Scientist / Analytics Engineer        | `data_scientist_analytics_engineer.v1`| `dr_rd/schemas/data_scientist_analytics_engineer_agent.json` | LIGHT | none | `self_check_minimal` |
| Fluorescence / Biological Sample Expert    | `fluorescence_biological_sample_expert.v1` | `dr_rd/schemas/fluorescence_biological_sample_expert_agent.json` | LIGHT | none | `self_check_minimal` |

## Migration Steps

1. **Remove inline prompts** in favour of `PromptFactory.build_prompt(spec)`.
2. **Reference the correct `io_schema_ref`** and enable JSON‑strict guardrails.
3. **Honor feature flags**: `RAG_ENABLED`, `ENABLE_LIVE_SEARCH`,
   `EVALUATORS_ENABLED`, `SAFETY_ENABLED`.
4. **Add evaluator/self‑repair and citations** when retrieval is used.

## Breaking Changes & Shims

None in this release; legacy agents emit runtime `DeprecationWarning` only.

## Validation Checklist

- Schema validates output.
- Sources present when retrieval ≠ `NONE`.
- Provenance events logged.

## Rollback

For rollback procedures see [ROLLBACK.md](ROLLBACK.md).
