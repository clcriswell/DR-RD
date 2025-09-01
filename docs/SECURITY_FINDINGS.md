# Security Findings

## Anonymization & Isolation
- Pseudonymization exists for planner inputs but not enforced for all agent prompts or logs.
- Recommendation: apply `pseudonymize_for_model` to all outbound LLM calls and redact logs using `redact_for_logging`.

## Key, IP & Header Rotation
- No proxy or key rotation in LLM or search clients; all requests use a single OpenAI key.
- Recommendation: introduce rotating API keys and proxy pools in `core/llm_client.py` and `dr_rd/retrieval/live_search.py` with per‑request randomized headers.

## Scanner Coverage
- `utils/safety` scans for prompt injection/PII but is not wired into orchestrator; no static code or file metadata scans.
- Recommendation: call `safety.check_text` on all agent outputs and integrate tools like `clamav`/`exiftool` for upload scanning.

## Logging & Telemetry
- Decision logs and evidence files stored unencrypted; telemetry relies on plain text cloud logging.
- Recommendation: encrypt logs at rest (SQLCipher or Vault) and hash chain decision log entries for immutability.

## TLS & Verification
- HTTP clients rely on defaults; no certificate pinning or explicit HTTPS enforcement.
- Recommendation: enable strict TLS verification and optional certificate pinning in `core/llm_client` and `dr_rd/retrieval` modules.
