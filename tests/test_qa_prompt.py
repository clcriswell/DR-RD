import json
import logging

from core.evaluation.self_check import PLACEHOLDER_RETRY_MSG, validate_and_retry
from utils.logging import log_placeholder_warning


def _qa_placeholder_payload():
    return {
        "role": "QA",
        "task": "t",
        "summary": "Not determined",
        "findings": "Not determined",
        "risks": ["Not determined"],
        "next_steps": ["Not determined"],
        "sources": ["Not determined"],
        "defects": [],
        "coverage": "Not determined",
    }


def test_qa_placeholder_output_logging(caplog):
    bad = json.dumps(_qa_placeholder_payload())
    calls: list[str] = []

    def retry_fn(reminder: str) -> str:
        calls.append(reminder)
        return bad

    with caplog.at_level(logging.WARNING):
        _, meta = validate_and_retry("QA", {"id": "t"}, bad, retry_fn, run_id="rid")
        assert meta["placeholder_failure"] is True
        open_issues = []
        run_state = {"has_failures": False}
        payload = json.loads(bad)
        log_placeholder_warning("rid", "QA", task_id="", note="post-retry placeholder result")
        log_placeholder_warning(
            "rid", "QA", task_id="", note="QA remained placeholder after two attempts"
        )
        open_issues.append(
            {
                "title": "QA analysis could not be completed after two attempts.",
                "role": "QA",
                "task_id": "",
                "result": payload,
            }
        )
        run_state["has_failures"] = True
    assert calls and calls[0] == PLACEHOLDER_RETRY_MSG
    assert run_state["has_failures"] is True
    assert open_issues
    assert any("agent_output_placeholder" in rec.message for rec in caplog.records)
