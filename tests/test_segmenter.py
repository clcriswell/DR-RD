from core.schemas import ConceptBrief
from planning.segmenter import segment_concept_brief


def test_segmenter_happy_path():
    brief = ConceptBrief(
        problem="Leakage of data",
        value="Secure system",
        users=["dev"],
        success_metrics=["Increase revenue"],
        risks=["none"],
        cost_range="0-1",
    )
    tasks = segment_concept_brief(brief)
    assert len(tasks) == 5
    assert all(task.role for task in tasks)


def test_segmenter_empty_fields():
    brief = ConceptBrief(
        problem="none",
        value="none",
        users=[],
        success_metrics=[],
        risks=[],
        cost_range="0-0",
    )
    tasks = segment_concept_brief(brief)
    assert tasks == []


def test_segmenter_applies_redaction():
    brief = ConceptBrief(
        problem="problem",
        value="value",
        users=["u"],
        success_metrics=["Contact test@example.com"],
        risks=[],
        cost_range="0-1",
    )
    tasks = segment_concept_brief(brief)
    assert any("[REDACTED:EMAIL]" in t.task for t in tasks)
