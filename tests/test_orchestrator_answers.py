import json

from utils.agent_json import extract_json_block


def _process(text):
    answers = {}
    role_to_findings = {}
    role = "QA"
    answers.setdefault(role, []).append(
        text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
    )
    obj = text if isinstance(text, (dict, list)) else extract_json_block(text)
    payload = obj or {}
    role_to_findings[role] = payload
    return answers, role_to_findings


def test_answers_join_no_concat_error():
    answers, _ = _process({"a": 1})
    answers.setdefault("QA", []).append("done")
    joined = "\n\n".join(answers["QA"])
    assert "\"a\": 1" in joined and "done" in joined


def test_payload_extraction_dict():
    _, findings = _process({"a": 1})
    assert findings["QA"] == {"a": 1}
