from dataclasses import dataclass
from typing import List, Optional, Protocol


@dataclass
class Snippet:
    text: str
    source: str


class Retriever(Protocol):
    def query(self, text: str, top_k: int) -> List[Snippet]: ...


def build_retriever(path: str | None = None) -> Optional[Retriever]:
    """Return default retriever if available.

    The underlying ``build_default_retriever`` now returns a tuple of
    ``(retriever, doc_count, dims)``.  This helper only exposes the retriever
    instance and quietly returns ``None`` if the FAISS bundle cannot be loaded.
    """

    try:
        from knowledge.faiss_store import build_default_retriever  # type: ignore

        retriever, _docs, _dims = (
            build_default_retriever(path=path)  # type: ignore[misc]
            if path is not None
            else build_default_retriever()
        )
        return retriever
    except Exception:
        return None
