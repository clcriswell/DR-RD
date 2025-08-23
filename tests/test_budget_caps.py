import os
import pytest

from core.retrieval.budget import get_web_max_calls


@pytest.mark.parametrize(
    "cfg, env, expected",
    [
        ({"web_search_max_calls": 5}, {}, 5),
        ({}, {"WEB_SEARCH_MAX_CALLS": "4"}, 4),
        ({}, {"LIVE_SEARCH_MAX_CALLS": "2"}, 2),
        ({"vector_index_present": False}, {}, 3),
        ({"vector_index_present": True}, {}, 3),
    ],
)
def test_get_web_max_calls(cfg, env, expected, monkeypatch):
    for key in ["WEB_SEARCH_MAX_CALLS", "LIVE_SEARCH_MAX_CALLS"]:
        if key in env:
            monkeypatch.setenv(key, env[key])
        else:
            monkeypatch.delenv(key, raising=False)
    assert get_web_max_calls(os.environ, cfg) == expected
