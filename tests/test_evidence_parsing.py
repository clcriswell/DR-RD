from utils.agent_json import extract_json_block

from core.observability import EvidenceSet


def test_extract_and_store():
    sample = 'Result:\n```json\n{"findings": "ok"}\n```'
    payload = extract_json_block(sample)
    assert isinstance(payload, dict)
    es = EvidenceSet(project_id="p1")
    es.add(role="r", task_title="t", claim=payload.get("findings"))
    assert es.items[0].claim == "ok"
