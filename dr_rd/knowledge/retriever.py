from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Tuple


class Retriever(ABC):
    """Abstract interface for retrieving relevant text snippets."""

    @abstractmethod
    def query(self, text: str, top_k: int) -> List[Tuple[str, str]]:
        """Return a list of (snippet, source) tuples for the given text."""
        raise NotImplementedError
