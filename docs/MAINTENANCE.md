# Maintenance Practices

## Issue Triage

Use labels: `bug`, `tech-debt`, `docs`, `perf`, `safety`, `ops`.

## Backporting

Critical fixes are backported to active LTS branches only.

## Updating Schemas

- Bump schema version and template id (`<role>.v{n}`).
- Document migration notes in `MIGRATION_GUIDE_v1_to_v2.md`.
- Update `PromptRegistry` entries accordingly.
- Maintain corresponding `*_fallback.json` schemas with relaxed validation used
  for retry flows. Finance, Research Scientist, and Materials Engineer now ship
  fallback schemas alongside their primary contracts, joining the existing CTO,
  Regulatory, and Marketing roles.

When an agent's response fails schema validation, the system retries using the
fallback schema and a prompt requesting a minimal JSON payload. If this second
attempt still fails validation, a fully populated placeholder JSON object is
returned so downstream consumers always receive compliant output.

## JSON Output Sanitization

Use `utils.agent_json.clean_json_payload` before validating agent responses.
This helper strips unknown keys, normalizes `sources`, removes markdown bullets
and joins multi-line strings, coerces strings/lists, and fills any missing
required fields with defaults. Running it keeps schema validation strict while
reducing manual repair work.

## On‑Call

See [ONCALL_RUNBOOK.md](ONCALL_RUNBOOK.md) for rotation details.

## Release Process

- Generate SBOM (`docs/SUPPLY_CHAIN.md`).
- Lock configuration (`scripts/freeze_config.py`).
- Update performance baselines.
- Record provenance and attestations.
