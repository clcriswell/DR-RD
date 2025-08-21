import time
from memory.memory_manager import MemoryManager


def test_session_isolation_and_ttl_expiry():
    mm = MemoryManager(ttl_default=1)
    mm.set("k", "v1", session_id="s1")
    mm.set("k", "v2", session_id="s2")
    assert mm.get("k", session_id="s1") == "v1"
    assert mm.get("k", session_id="s2") == "v2"
    time.sleep(1.2)
    assert mm.get("k", session_id="s1") is None
    assert mm.get("k", session_id="s2") is None
    mm.set("k", "v", session_id="s1", ttl_seconds=10)
    removed = mm.prune()
    assert removed == 0
    mm.delete("k", session_id="s1")
    assert mm.get("k", session_id="s1") is None
