from pathlib import Path
import yaml


def test_concept_brief_template_exists():
    assert Path('docs/concept_brief.md').exists()


def test_role_cards_exist():
    roles_dir = Path('docs/roles')
    required = {
        'role_planner.md',
        'role_researcher.md',
        'role_orchestrator.md',
        'role_evaluator.md',
    }
    existing = {p.name for p in roles_dir.glob('*.md')}
    assert required.issubset(existing)


def test_task_segmentation_plan_schema():
    plan = yaml.safe_load(Path('planning/task_plan.yaml').read_text())
    assert {'roles', 'tasks', 'inputs', 'outputs', 'redaction_policy'} <= plan.keys()
    assert isinstance(plan['roles'], dict)
    assert isinstance(plan['tasks'], list)
    for task in plan['tasks']:
        assert {'id', 'inputs', 'outputs'} <= task.keys()


def test_planning_prompts_include_redaction():
    prompt_dir = Path('prompts/planning')
    for prompt_file in prompt_dir.glob('*.md'):
        text = prompt_file.read_text().lower()
        assert 'redaction' in text
