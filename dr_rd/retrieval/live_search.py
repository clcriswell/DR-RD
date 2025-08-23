from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Protocol, Tuple

from utils.search_tools import search_google, summarize_search

from core.llm_client import call_openai


@dataclass
class Source:
    title: str
    url: str | None = None


class LiveSearchClient(Protocol):
    def search_and_summarize(
        self, query: str, k: int, max_tokens: int
    ) -> Tuple[str, List[Source]]: ...


class OpenAIWebSearchClient:
    def search_and_summarize(
        self, query: str, k: int, max_tokens: int
    ) -> Tuple[str, List[Source]]:
        messages = [{"role": "user", "content": query}]
        result = call_openai(
            model="gpt-4.1-mini",
            messages=messages,
            tools=[{"type": "web_search"}],
            max_output_tokens=max_tokens,
        )
        text = result.get("text") or ""
        sources = []
        resp = result.get("raw")
        try:
            for item in getattr(resp, "references", []) or []:
                sources.append(Source(title=item.get("title", ""), url=item.get("url")))
        except Exception:
            pass
        return text, sources


class SerpAPIClient:
    def search_and_summarize(
        self, query: str, k: int, max_tokens: int
    ) -> Tuple[str, List[Source]]:
        results = search_google("live", "", query, k=k)
        snippets = [r.get("snippet", "") for r in results]
        summary = summarize_search(snippets, model="gpt-4.1-mini")
        sources = [Source(title=r.get("title", ""), url=r.get("link")) for r in results]
        return summary, sources


BACKENDS = {
    "openai": OpenAIWebSearchClient,
    "serpapi": SerpAPIClient,
}


def get_live_client(backend: str) -> LiveSearchClient:
    cls = BACKENDS.get(backend, OpenAIWebSearchClient)
    return cls()
