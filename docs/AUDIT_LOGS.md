# Audit Logs

DR-RD writes append-only audit logs for key tenant events. Logs are stored under
`~/.dr_rd/tenants/<org>/<workspace>/audit/audit.jsonl` and each entry is chained
using an HMAC hash to provide tamper evidence.

## Record Format
```
{ "ts": <unix>, "actor": "p1", "action": "run", "resource": "tool", 
  "outcome": "ok", "details_hash": "...", "prev_hash": "...", "hash": "..." }
```
`details_hash` is the HMAC of a JSON serialisation of any additional metadata.
`prev_hash` links to the previous entry. The secret key is provided via the
`AUDIT_HMAC_KEY` environment variable.

## Verification
`scripts/audit_verify.py` can verify the hash chain and summarise the log.
Tampering with any record breaks the chain.
