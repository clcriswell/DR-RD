# Summarization

DR-RD performs synthesis in two lightweight passes:

1. **Role summarization** – each agent's raw findings are condensed into a `RoleSummary` schema
   of up to five bullet points.
2. **Integration** – the collection of `RoleSummary` objects is analyzed to produce a
   holistic `IntegratedSummary` with a `plan_summary`, combined `key_findings`, and any
   cross‑role `contradictions`.

Environment variables allow quick overrides:

- `SYNTH_TWO_PASS` (default `true`): set to `false` to skip summarization entirely.
- `SYNTH_CROSS_REFERENCE` (default `true`): set to `false` to omit contradiction checks.

This summarization stage fits between execution and final synthesis within the project's
three‑stage pipeline (planning → execution → synthesis), ensuring contributors see concise
results while the UI remains thin.
