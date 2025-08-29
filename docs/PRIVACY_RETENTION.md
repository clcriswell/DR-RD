# Privacy & Retention

The system applies per-artifact TTLs and lightweight PII scrubbing as defined in
`config/retention.yaml`. Tenants may override values via
`config/tenants/{org}/{workspace}/retention.yaml` (not checked into git).

Subject identifiers (e.g. `email`, `user_id`) are hashed with an environment
salt (`PRIVACY_SALT`) to produce stable subject keys. These keys drive retention,
redaction and export flows.

Redactions are append-only: audit and provenance logs record `REDACTION` events
that preserve the hash chain while masking sensitive strings. Receipts for all
operations are written under
`~/.dr_rd/tenants/{org}/{workspace}/privacy/receipts/`.

Exports produce portable bundles for tenants or individual subjects and include
a `manifest.json` describing the components and schema versions.
