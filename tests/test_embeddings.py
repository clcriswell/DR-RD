import os
import pytest

from utils.embeddings import embed_texts


def test_openai_no_key(monkeypatch):
    if os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY set")
    out = embed_texts(["hi"], provider="openai", model="x")
    assert out is None


def test_local_no_pkg():
    try:
        import sentence_transformers  # type: ignore
        pytest.skip("sentence_transformers installed")
    except Exception:
        pass
    out = embed_texts(["hi"], provider="local", model="")
    assert out is None
