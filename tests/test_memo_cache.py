from dr_rd.cache import file_cache
from core.llm import memo_cache


def test_cache_hit_and_ttl(monkeypatch):
    monkeypatch.setattr(memo_cache, "_cfg", {"enabled": True, "ttl_s": 1})
    prompt = {"system": "s", "user": "u"}
    h = memo_cache.prompt_hash(prompt)
    memo_cache.put(h, "openai/gpt", {"text": "ok"})
    assert memo_cache.get(h, "openai/gpt") == {"text": "ok"}
    now = file_cache.time.time()
    monkeypatch.setattr(file_cache.time, "time", lambda: now + 2)
    assert memo_cache.get(h, "openai/gpt") is None
