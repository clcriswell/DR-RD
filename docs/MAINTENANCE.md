# Maintenance Practices

## Issue Triage

Use labels: `bug`, `tech-debt`, `docs`, `perf`, `safety`, `ops`.

## Backporting

Critical fixes are backported to active LTS branches only.

## Updating Schemas

- Bump schema version and template id (`<role>.v{n}`).
- Document migration notes in `MIGRATION_GUIDE_v1_to_v2.md`.
- Update `PromptRegistry` entries accordingly.

## On‑Call

See [ONCALL_RUNBOOK.md](ONCALL_RUNBOOK.md) for rotation details.

## Release Process

- Generate SBOM (`docs/SUPPLY_CHAIN.md`).
- Lock configuration (`scripts/freeze_config.py`).
- Update performance baselines.
- Record provenance and attestations.
