import time
from utils import idempotency


def test_key_consistent():
    p = {"messages": [{"role": "user", "content": "hi"}]}
    k1 = idempotency.key('openai', 'gpt', p)
    k2 = idempotency.key('openai', 'gpt', p)
    assert k1 == k2


def test_cache_ttl(tmp_path, monkeypatch):
    monkeypatch.setattr(idempotency, 'ROOT', tmp_path)
    idempotency.ROOT.mkdir(parents=True, exist_ok=True)
    k = 'abc'
    idempotency.put(k, {'a':1})
    assert idempotency.get(k, ttl_sec=1) == {'a':1}
    time.sleep(1.2)
    assert idempotency.get(k, ttl_sec=1) is None
