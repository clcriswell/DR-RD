from __future__ import annotations

"""Live web search helpers with OpenAI and SerpAPI backends.

This module exposes both a modern ``run_live_search_with_fallback`` helper as
well as legacy ``get_live_client`` utilities used in earlier tests.  The modern
API returns simple dictionaries while the legacy API works with ``Source``
dataclasses and ``search_and_summarize`` tuples.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional, Protocol
import json
import logging
import httpx

from core.llm_client import call_openai
from utils.search_tools import search_google, summarize_search

from dr_rd.config.env import get_env

log = logging.getLogger("drrd")


# ---------------------------------------------------------------------------
# Data containers -----------------------------------------------------------


@dataclass
class Source:
    """Simple representation of a search result used by legacy callers."""

    title: str
    url: str | None = None
    snippet: str | None = None


class LiveSearchClient(Protocol):
    """Legacy search client protocol."""

    def search_and_summarize(self, query: str, k: int, max_tokens: int) -> Tuple[str, List[Source]]:
        ...


# ---------------------------------------------------------------------------
# Modern implementation -----------------------------------------------------


class OpenAIWebSearchUnavailable(RuntimeError):
    """Raised when the OpenAI web_search tool is not available."""


def _is_openai_web_search_unavailable(err: Exception) -> bool:
    """Heuristics for Responses API/tooling not available errors."""

    s = str(err).lower()
    return any(
        k in s
        for k in [
            "web_search",
            "tool is not enabled",
            "not authorized",
            "unknown tool",
            "response_format not supported",
            "400",
            "403",
            "404",
        ]
    )


class OpenAIWebSearchClient:
    """Client using OpenAI's ``web_search`` tool."""

    def __init__(self, model: str = "gpt-4.1-mini"):
        self.model = model

    def search_and_summarize(
        self,
        query: str,
        k: int | None = None,
        max_tokens: int | None = None,
        max_sources: int = 5,
        *,
        tools: list[dict] | None = None,
        tool_choice: str | None = None,
    ) -> Any:
        if k is not None:
            max_sources = k
        try:
            kwargs: dict = {"tools": tools or [{"type": "web_search"}]}
            if tool_choice is not None:
                kwargs["tool_choice"] = tool_choice
            rsp = call_openai(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You perform web research and give concise, source-backed summaries.",
                    },
                    {
                        "role": "user",
                        "content": f"Search the web and summarize reliably with sources: {query}",
                    },
                ],
                **kwargs,
            )
        except Exception as e:  # pragma: no cover - network failures
            if _is_openai_web_search_unavailable(e):
                log.warning("OpenAI web_search tool unavailable; will fallback: %s", e)
                raise OpenAIWebSearchUnavailable(str(e)) from e
            raise

        text = rsp.get("text") or rsp.get("content") or ""
        sources = rsp.get("references") or rsp.get("sources") or []
        if not sources:
            raw = rsp.get("raw")
            try:
                sources = [
                    {"title": item.get("title"), "url": item.get("url")}
                    for item in getattr(raw, "references", []) or []
                ]
            except Exception:
                sources = []
        if isinstance(sources, list) and max_sources > 0:
            sources = sources[:max_sources]
        if k is not None or max_tokens is not None:
            srcs = [Source(title=s.get("title", ""), url=s.get("url")) for s in sources]
            return text, srcs
        return {"text": text, "sources": sources}


class SerpAPIWebSearchClient:
    """Minimal SerpAPI client that lets the LLM summarize results."""

    def __init__(self, llm_model: str, api_key: Optional[str] = None):
        self.llm_model = llm_model
        self.api_key = api_key or get_env("SERPAPI_API_KEY")
        if not self.api_key:
            raise RuntimeError("SERPAPI_API_KEY missing; cannot use SerpAPI fallback.")

    def search_and_summarize(self, query: str, num: int = 6) -> Dict[str, Any]:
        params = {"engine": "google", "q": query, "num": num, "api_key": self.api_key}
        with httpx.Client(timeout=30) as client:
            r = client.get("https://serpapi.com/search.json", params=params)
            r.raise_for_status()
            data = r.json()

        items: List[Dict[str, str]] = []
        for item in (data.get("organic_results") or []):
            title = item.get("title")
            link = item.get("link")
            snippet = item.get("snippet")
            if title and link:
                items.append({"title": title, "url": link, "snippet": snippet or ""})

        prompt = [
            {
                "role": "system",
                "content": "You summarize search results into a compact, source-cited brief.",
            },
            {
                "role": "user",
                "content": (
                    f"Query: {query}\n\nResults:\n{json.dumps(items, ensure_ascii=False, indent=2)}\n\n"
                    "Write a short summary with bullet points and include inline [#] markers. "
                    "Then list the sources with title and URL."
                ),
            },
        ]
        rsp = call_openai(self.llm_model, messages=prompt)
        text = rsp.get("text") or rsp.get("content") or ""
        return {"text": text, "sources": items}


def run_live_search_with_fallback(
    query: str,
    llm_model: str,
    backend_primary: str = "openai",
    allow_serpapi_fallback: bool = True,
    max_sources: int = 5,
) -> Dict[str, Any]:
    """Try OpenAI first, then fall back to SerpAPI if configured."""

    last_err: Optional[Exception] = None

    if backend_primary == "openai":
        try:
            res = OpenAIWebSearchClient(llm_model).search_and_summarize(
                query, max_sources=max_sources
            )
            log.info(
                "OpenAIWebSearchUsed query=%r sources=%d", query, len(res.get("sources") or [])
            )
            return res
        except OpenAIWebSearchUnavailable as e:
            last_err = e
        except Exception as e:  # pragma: no cover - network failures
            log.warning("OpenAI web search error; will consider fallback: %s", e)
            last_err = e

        if allow_serpapi_fallback:
            try:
                res = SerpAPIWebSearchClient(llm_model).search_and_summarize(query)
                log.info(
                    "SerpAPIFallbackUsed query=%r sources=%d",
                    query,
                    len(res.get("sources") or []),
                )
                return res
            except Exception as e2:  # pragma: no cover - network failures
                last_err = e2
                log.error("SerpAPI fallback failed: %s", e2)
                raise last_err
        else:
            raise last_err or RuntimeError(
                "OpenAI web search unavailable and fallback disabled."
            )

    elif backend_primary == "serpapi":
        res = SerpAPIWebSearchClient(llm_model).search_and_summarize(query)
        log.info(
            "SerpAPIPrimaryUsed query=%r sources=%d", query, len(res.get("sources") or [])
        )
        return res

    else:
        raise ValueError(f"Unknown live search backend: {backend_primary}")


# ---------------------------------------------------------------------------
# Legacy adapters -----------------------------------------------------------


class SerpAPIClient:
    """Historic SerpAPI client using plain Google results + LLM summarization."""

    def search_and_summarize(self, query: str, k: int, max_tokens: int) -> Tuple[str, List[Source]]:
        results = search_google("live", "", query, k=k)
        snippets = [r.get("snippet", "") for r in results]
        summary = summarize_search(snippets, model="gpt-4.1-mini")
        sources = [Source(title=r.get("title", ""), url=r.get("link")) for r in results]
        return summary, sources
BACKENDS: Dict[str, type[LiveSearchClient]] = {
    "openai": OpenAIWebSearchClient,
    "serpapi": SerpAPIClient,
}


def get_live_client(backend: str) -> LiveSearchClient:
    """Return a live search client implementation."""

    cls = BACKENDS.get(backend, OpenAIWebSearchClient)
    return cls()

