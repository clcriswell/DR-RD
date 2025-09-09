import json
from core.evaluation.self_check import validate_and_retry, PLACEHOLDER_RETRY_MSG


def _build_payload(name, url):
    return {
        "role": "Materials Engineer",
        "task": "t",
        "summary": "s",
        "findings": "f",
        "properties": [
            {
                "name": name,
                "property": "density",
                "value": 1,
                "units": "g/cm3",
                "source": url,
            }
        ],
        "tradeoffs": [],
        "risks": ["r"],
        "next_steps": ["n"],
        "sources": [url],
    }


def test_placeholder_triggers_retry_and_escalates():
    bad = json.dumps(_build_payload("Material A", "https://example.com/foo"))
    calls = []

    def retry_fn(reminder: str) -> str:
        calls.append(reminder)
        return bad

    _, meta = validate_and_retry("Materials Engineer", {"title": "t"}, bad, retry_fn)
    assert calls and calls[0] == PLACEHOLDER_RETRY_MSG
    assert meta["retried"] is True
    assert meta["valid_json"] is False
    assert meta["placeholder_failure"] is True
