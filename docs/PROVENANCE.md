# Provenance Logging

Tool invocations are logged when `PROVENANCE_ENABLED` is true (default). Each call records agent, tool name, hashed inputs and outputs, token count if known, and wall-clock time. Events are appended to `runs/<timestamp>/provenance.jsonl` and are accessible in memory via `core.provenance.get_events()`.

Arguments and outputs are SHA256 hashes of compact JSON to avoid leaking sensitive payloads.
