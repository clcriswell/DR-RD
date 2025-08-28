# Safety & Governance

This module layers policy enforcement and content filters over agent outputs.

## Policies
Policies are defined in `dr_rd/policy/policies.yaml` and describe actions for
classes such as `pii`, `secrets`, `toxicity`, `license`, `brand`, and
`compliance`. Actions may `block`, `redact`, or `allow` content. Decisions are
reported via `PolicyDecision` with fields `{allowed, redactions, violations, notes}`.

## Filters
`dr_rd/safety/filters.py` detects PII, secrets, toxicity, and license issues and
redacts sensitive values. `filter_output` walks JSON structures, sanitizing only
string fields while preserving shape.

## Repair Path
`core/safety_gate.guard_output` runs filters after model output. Blocked content
triggers a single sanitize retry. When `EVALUATORS_ENABLED=true` one evaluator
retry is permitted before returning `{"error": "SAFETY_BLOCKED"}`.

## Evaluator Hooks
Lightweight evaluators (`evaluators/*.py`) can gate retries or validate final
outputs for PII leaks, toxicity, citation integrity, and jailbreak resilience.

## Provenance
Agents attach `safety_meta` to outputs. The Synthesizer aggregates this data and
notes blocked items in `contradictions` while adjusting confidence.

## Redaction Review

`dr_rd/safety/redaction_review.py` summarises redactions by type using hashed
examples only. The review workflow never surfaces raw text, enabling safe audit
of filters without recovering sensitive content.

## Configuration
Feature flags live in `config/feature_flags.py` and defaults in
`config/safety.yaml`. See `docs/CONFIG.md` for details.
