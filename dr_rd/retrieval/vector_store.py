from dataclasses import dataclass
from typing import List, Protocol

@dataclass
class Snippet:
    text: str
    source: str

class Retriever(Protocol):
    def query(self, text: str, top_k: int) -> List[Snippet]:
        ...

class _DummyRetriever:
    def query(self, text: str, top_k: int) -> List[Snippet]:
        return []

def build_retriever() -> Retriever:
    """Return default retriever or a dummy fallback."""
    try:
        from knowledge.faiss_store import build_default_retriever
        ret = build_default_retriever()
        if ret:
            return ret  # type: ignore[return-value]
    except Exception:
        pass
    return _DummyRetriever()
