import json

from utils.errors import SafeError, as_json


def test_as_json_serializes_sets_deterministically():
    err = SafeError(
        kind="test",
        user_message="u",
        tech_message="t",
        traceback=None,
        support_id="id",
        context={
            "simple": {3, 1, 2},
            "nested": {"inner": {5, 4}},
            "list": [{2, 1}],
            "tuple": ({3, 1}, {4, 2}),
        },
    )
    data = json.loads(as_json(err))
    ctx = data["context"]
    assert ctx["simple"] == [1, 2, 3]
    assert ctx["nested"]["inner"] == [4, 5]
    assert ctx["list"][0] == [1, 2]
    assert ctx["tuple"][0] == [1, 3]
    assert ctx["tuple"][1] == [2, 4]
