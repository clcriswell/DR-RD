"""Simple OpenAI embedding wrapper with cache."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict

from dr_rd.config.env import get_env

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None

from dr_rd.cache.file_cache import FileCache

CACHE_DIR = Path(".dr_rd_cache/embed")
cache = FileCache(str(CACHE_DIR))


def _hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def embed(text: str) -> Dict[str, float] | None:
    if not OpenAI or not get_env("OPENAI_API_KEY"):
        return None
    key = _hash(text)
    cached = cache.get(key)
    if cached:
        return json.loads(cached)
    client = OpenAI()
    vec = client.embeddings.create(model="text-embedding-3-small", input=text)
    arr = {str(i): v for i, v in enumerate(vec.data[0].embedding)}
    cache.put(key, json.dumps(arr))
    return arr
