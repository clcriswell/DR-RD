from core.summarization.role_summarizer import summarize_role
from core.summarization.schemas import RoleSummary


def test_role_summarizer_truncates_to_five_bullets():
    agent_json = {
        "role": "Engineer",
        "findings": [f"Point {i}" for i in range(1, 8)],
    }
    summary = summarize_role(agent_json)
    assert isinstance(summary, RoleSummary)
    assert len(summary.bullets) == 5
