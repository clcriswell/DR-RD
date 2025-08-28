# Agent Trace UX

The Agent Trace panel exposes execution traces and cross‑run diffing.

## Run Selection
- Pick a **Base** and **Candidate** run from the run directory list.
- Runs are discovered from `runs/*/run_meta.json`.

## Diff Semantics
- Added/removed/changed spans are computed by matching span ids.
- Roll‑ups include total latency delta and tool failure rate.

## Severity Rules
Diagnostics apply thresholds from `config/diagnostics.yaml`:
- `latency.warn_ms` / `latency.fail_ms`
- `failure_rate.warn_delta` / `failure_rate.fail_delta`

## Exports
- `trace_diff.json` – raw diff output.
- `incident_<timestamp>.zip` – bundle with run data and diagnostics summary.
