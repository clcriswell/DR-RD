# Alerting

Telemetry events feed SLO calculations in `scripts/slo_check.py`.
Breaches raise GitHub issues and optionally notify Slack.

## SLO Targets
- Availability: 99%
- Quality: 95% of retrieval runs include citations
- Validity: 98% schema valid
- Latency p95: plan 1s, exec 2s, synth 1.5s

Use `scripts/raise_github_issue.py` to acknowledge and resolve alerts.
