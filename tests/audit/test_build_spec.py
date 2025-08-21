from pathlib import Path
import yaml


def test_system_design_doc_sections():
    content = Path('docs/ARCHITECTURE.md').read_text().lower()
    for word in ('components', 'interfaces', 'data flow', 'risks'):
        assert word in content


def test_build_spec_exists():
    assert Path('docs/build_spec.md').exists()


def test_work_plan_structure():
    path = Path('docs/work_plan.yaml')
    assert path.exists()
    plan = yaml.safe_load(path.read_text())
    assert {'milestones', 'owners', 'estimates', 'decision_log'} <= plan.keys()
