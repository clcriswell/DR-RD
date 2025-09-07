import json

from utils.errors import SafeError, as_json


def test_as_json_handles_sets_and_tuples():
    err = SafeError(
        kind="k",
        user_message="u",
        tech_message="t",
        traceback=None,
        support_id="s",
        context={"a": {2, 1}, "b": (1, 2), "c": [{"d": {3, 1}}]},
    )
    data = as_json(err)
    obj = json.loads(data.decode("utf-8"))
    assert obj["context"]["a"] == [1, 2]
    assert obj["context"]["b"] == [1, 2]
    assert obj["context"]["c"][0]["d"] == [1, 3]
