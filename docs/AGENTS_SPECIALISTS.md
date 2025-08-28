# Specialist Agents

Three specialist roles are available:

- **Materials** – default retrieval *LIGHT* with citations when retrieval is enabled. Tools: `lookup_materials`.
- **QA** – default retrieval *NONE* (enable LIGHT only when artifacts are missing and RAG flags on). Tools: `build_requirements_matrix`, `compute_test_coverage`, `classify_defects`.
- **Finance Specialist** – default retrieval *NONE*. Tools: `calc_unit_economics`, `npv`, `monte_carlo`.

Each specialist consumes prompts via `PromptFactory` and returns JSON matching its schema in `dr_rd/schemas/` with no free-text leakage.
