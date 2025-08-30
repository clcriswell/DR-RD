from utils.run_id import new_run_id, is_run_id


def test_new_run_id_unique_and_valid():
    ids = {new_run_id() for _ in range(5)}
    assert len(ids) == 5
    for rid in ids:
        assert is_run_id(rid)
    assert not is_run_id("bad-id")
