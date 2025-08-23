from dataclasses import dataclass
from typing import List, Optional, Protocol


@dataclass
class Snippet:
    text: str
    source: str


class Retriever(Protocol):
    def query(self, text: str, top_k: int) -> List[Snippet]: ...


def build_retriever(path: str | None = None) -> Optional[Retriever]:
    """Return default retriever if available."""
    try:
        from knowledge.faiss_store import build_default_retriever  # type: ignore

        return (
            build_default_retriever(path=path)  # type: ignore[return-value]
            if path is not None
            else build_default_retriever()  # type: ignore[return-value]
        )
    except Exception:
        return None
