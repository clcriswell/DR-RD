import json

from core.orchestrator import _to_text


def test_answer_aggregation_and_render():
    answers: dict[str, list[str]] = {}
    answers.setdefault("Role", []).append(_to_text("hello"))
    answers.setdefault("Role", []).append(_to_text({"a": 1}))
    joined = {k: "\n\n".join(v) for k, v in answers.items()}
    assert joined["Role"] == "hello\n\n" + json.dumps({"a": 1}, ensure_ascii=False)

