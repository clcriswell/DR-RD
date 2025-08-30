import shutil
from utils.storage import _create_storage, key_run


def test_local_roundtrip():
    conf = {"backend": "local", "prefix": "test_storage"}
    st = _create_storage(conf)
    key = key_run("r1", "trace", "json")
    data = b"hello"
    st.write_bytes(key, data)
    assert st.read_bytes(key) == data
    assert st.exists(key)
    refs = list(st.list("runs/r1"))
    assert any(r.key == key for r in refs)
    st.delete(key)
    assert not st.exists(key)
    assert st.url_for(key, 60) is None
    shutil.rmtree(f".{conf['prefix']}", ignore_errors=True)
