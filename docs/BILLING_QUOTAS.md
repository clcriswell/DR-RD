# Billing and Quotas

Usage metering and budgeting are enabled when `BILLING_ENABLED` and
`QUOTAS_ENABLED` are true. Configuration lives in `config/billing.yaml` and can
be overridden per tenant via `config/tenants/{org}/{workspace}/billing.yaml`.

## Free Tier
- `monthly_tokens_in`
- `monthly_tokens_out`
- `monthly_tool_runtime_ms`
- `monthly_tool_calls`

## Quotas
Soft and hard quotas are defined for tokens and tool usage. Approaching soft
quotas should trigger graceful degradation while hard quotas block new runs.

## Artifacts
Monthly usage files and summaries are written under
`.dr_rd/tenants/{org}/{workspace}/billing/`:
- `usage_YYYY-MM.jsonl`
- `summary_YYYY-MM.json`

These files feed into invoice generation and quota checks.
