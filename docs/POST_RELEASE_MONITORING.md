# Post-Release Monitoring

1. **Telemetry** – instrumentation records counters and latency to `.dr_rd/telemetry`.
2. **SLOs** – `scripts/slo_check.py` aggregates metrics and computes budgets.
3. **Alerting** – GitHub Actions run the check and open issues on breach.
4. **On‑Call** – responders follow `docs/ONCALL_RUNBOOK.md`.
5. **Rollback** – if necessary, see `docs/ROLLBACK.md`.
