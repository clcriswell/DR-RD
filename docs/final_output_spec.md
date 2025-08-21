# Final Output Specification

The final report must contain the following sections:

- Executive Summary
- Problem & Value
- Research Findings
- Risks & Unknowns
- Architecture & Interfaces
- Regulatory & Compliance
- IP & Prior Art
- Market & GTM
- Cost Overview
- Next Steps

Deterministic controls:

- Set `DRRD_SEED` to seed any internal randomness.
- LLM calls accept `seed` and `temperature` parameters. In `test` mode, temperature defaults to `0.0`.

Artifacts produced after synthesis are written to:

- `audits/<slug>/final/final_report.md`
- `audits/<slug>/final/appendices_map.json`
- `audits/<slug>/final/traceability_matrix.csv`
- `audits/<slug>/final/final_bundle.zip`
