# Plan v1 Audit

## Summary
Concept planning artifacts are largely absent. The repository lacks templates, role definitions, structured task plans with inputs/outputs, and redaction guidance.
## Checklist
- [FAIL] 1.1 Concept brief template exists
- [FAIL] 1.2 Role cards exist for Planner/PM and other agents
- [FAIL] 1.3 Task segmentation plan exists as structured data
- [FAIL] 1.4 Redaction policy bound into planning prompts

## Evidence
- `docs/concept_brief.md` not found
- `docs/roles/` directory missing
- No task plan YAML or JSON under `planning/`; structure for inputs/outputs cannot be verified
- Planning prompts lack redaction mentions
- Failing tests:
  - `tests/audit/test_plan_v1.py::test_concept_brief_template_exists`
  - `tests/audit/test_plan_v1.py::test_role_cards_exist`
  - `tests/audit/test_plan_v1.py::test_task_segmentation_plan_structure`
  - `tests/audit/test_plan_v1.py::test_redaction_policy_bound_in_planning_prompts`

## Gaps
- Missing concept brief template
- No role cards or agent definitions
- Planning lacks structured task segmentation
- Redaction policy not integrated into prompts

## Minimal Fix Suggestions
- Add `docs/concept_brief.md` template
- Create `docs/roles/` with role card markdown files
- Introduce YAML/JSON task plan defining roles, tasks, inputs, and outputs
- Embed redaction policy references in planning prompts

