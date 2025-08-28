# Incident Bundles

Incident bundles capture regressions for offline analysis.

## Contents
- Base and candidate `run_meta.json` and `provenance.jsonl`.
- `trace_diff.json` describing span changes.
- `diagnostics.json` summarising rule evaluation.
- `README.md` with basic usage instructions.

Bundles are zipped as `incident_<YYYYmmdd_HHMMSS>.zip`.

## Sanitization
Only hashed examples and counts are included for redactions. Raw sensitive
content is never stored.
