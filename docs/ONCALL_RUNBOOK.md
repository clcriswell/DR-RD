# On-Call Runbook

## Severity
- **SEV1** – complete outage. Page immediately.
- **SEV2** – partial outage or major regression. Page within 15 minutes.
- **SEV3** – minor issue. Triage during business hours.

## Triage Checklist
1. Confirm alert details in telemetry and GitHub issue.
2. Check recent runs and provenance logs in `runs/`.
3. Collect a support bundle with `scripts/collect_support_bundle.py`.

## Quick Mitigations
- Use `scripts/toggle_safe_mode.py` to disable risky features.
- Downshift retrieval or model routing via feature flags.
- Disable evaluators if causing failures.

## Escalation
- Post updates in the team channel.
- Escalate to component owners if unresolved.
