# Security & Privacy

This application follows a few simple rules to keep data safe.

## Secret Management
Secrets are resolved from environment variables first and then from `st.secrets`.
Call `utils.secrets.get()` or `require()` to access them. Values are never
logged and can be typed via a casting function.

## Redaction
All logs, errors and exports pass through regex-based scrubbing that masks
access tokens and common PII such as emails, phone numbers and credit card
numbers. Dictionaries are traversed recursively and long values are truncated
before writing.

## Upload Policy
Uploads are limited to a small set of MIME types and a maximum size of 20 MB.
Text files are scanned for PII; flagged items show a small warning badge in the
UI. Disallowed types are rejected before storage.

## Repository Scanning
`scripts/scan_repo_secrets.py` walks the repository (excluding `.dr_rd/` and
`node_modules`) looking for known token patterns and high-entropy strings.
The script prints any findings and exits non‑zero if secrets are discovered.

## Privacy Export & Purge
`scripts/privacy_export.py --run-id <id> --out <dir>` creates a bundle
containing the run folder and any telemetry events for that run after
re-applying redaction. Generated data can then be handed to users or removed.
