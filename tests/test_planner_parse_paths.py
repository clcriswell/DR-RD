import json
from types import SimpleNamespace

from core.llm_client import extract_planner_payload


def test_extract_parsed_path():
    resp = SimpleNamespace(
        output=[
            SimpleNamespace(
                type="message",
                content=[
                    SimpleNamespace(parsed={"tasks": [
                        {"role": "a", "title": "b", "description": "c"}
                    ]})
                ],
            )
        ]
    )
    data = extract_planner_payload(resp)
    assert data == {"tasks": [{"role": "a", "title": "b", "description": "c"}]}


def test_extract_text_path():
    payload = {"tasks": []}
    resp = SimpleNamespace(output=[], output_text="```json\n{}\n```".format(
        json.dumps(payload)
    ))
    data = extract_planner_payload(resp)
    assert data == payload


def test_extract_chat_path():
    payload = {"tasks": []}
    resp = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))]
    )
    data = extract_planner_payload(resp)
    assert data == payload

