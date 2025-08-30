# Integrations

Configure optional notification channels for Slack, email, or a generic webhook.

## Slack
1. Create an *Incoming Webhook* in Slack and copy the URL.
2. Store the value in `SLACK_WEBHOOK_URL` via environment variable or `st.secrets`.
3. In the Notifications page, enable Slack and optionally set a mention such as `@here`.

## Email
1. Provide SMTP credentials via secrets:
   - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`
   - Optional `SMTP_TLS=1` to enable TLS (default).
2. Add recipient addresses in preferences. Up to ten addresses are allowed.

## Webhook
1. Set `WEBHOOK_URL` to receive JSON payloads of run events.
2. Optionally set `WEBHOOK_SECRET` to sign requests. The body HMAC SHA-256 is sent in `X-DRRD-Signature`.

### Security
Secrets should be stored in environment variables or `st.secrets`; they are never written to prefs. Webhooks should verify the `X-DRRD-Signature` header when a secret is configured.

### Examples
Slack messages use block kit and include run ID, status, mode, and cost. Webhook payload example:
```json
{
  "ts": 1234567890.0,
  "event": "run_completed",
  "run_id": "r1",
  "status": "success",
  "mode": "standard",
  "totals": {"tokens": 1000, "cost_usd": 0.02}
}
```

### Troubleshooting
- Ensure network egress to Slack/SMTP/webhook endpoints.
- Check rate limits for external services.
- Use the "Send test" buttons in the Notifications settings page.


## Artifact storage

Configure storage backend for run artifacts. Supported backends are local filesystem, S3, and GCS.
Set non-secret preferences under the Storage settings page. Secrets like credentials should be provided via environment variables or st.secrets.
Signed download URLs are generated when supported, with lifetime controlled by `signed_url_ttl_sec`.
