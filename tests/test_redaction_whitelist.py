from core.redaction import Redactor


def test_role_names_not_redacted():
    text = (
        "CTO, Marketing Analyst, Dynamic Specialist, QA, Regulatory, "
        "Finance, Materials Engineer, Research Scientist, Planner"
    )
    red, _, _ = Redactor().redact(text, mode="heavy")
    for role in [
        "CTO",
        "Marketing Analyst",
        "Dynamic Specialist",
        "QA",
        "Regulatory",
        "Finance",
        "Materials Engineer",
        "Research Scientist",
        "Planner",
    ]:
        assert role in red
