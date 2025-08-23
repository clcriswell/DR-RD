import json
from unittest.mock import Mock, patch

import pytest

from orchestrators.app_builder import plan_app_spec


def _make_response(text: str):
    return {"text": text, "raw": {}}


@pytest.mark.timeout(30)
@patch("orchestrators.app_builder.call_openai")
def test_plan_app_spec_returns_json(mock_call):
    valid_json = json.dumps(
        {
            "name": "My App",
            "description": "Demo",
            "pages": [{"name": "Home", "purpose": "Start"}],
            "python_packages": ["pandas"],
        }
    )
    mock_call.side_effect = [_make_response("not json"), _make_response(valid_json)]

    spec = plan_app_spec("demo idea")

    assert spec.name == "My App"
    assert spec.description == "Demo"
    assert spec.pages and spec.pages[0].name == "Home"
    assert "pandas" in spec.python_packages
    assert mock_call.call_count == 2
