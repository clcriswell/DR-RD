from typing import Any, Dict, List, Tuple
import os
import logging

from dr_rd.config.env import get_env

from core.llm_client import call_openai

log = logging.getLogger("drrd")


class WebSearchError(RuntimeError):
    pass


def _norm_max_calls() -> int:
    val = os.getenv("WEB_SEARCH_MAX_CALLS") or os.getenv("LIVE_SEARCH_MAX_CALLS")
    try:
        v = int(val) if val is not None else None
    except Exception:
        v = None
    return v if (v and v > 0) else 3


def openai_web_search(query: str, *, max_results: int = 5) -> Dict[str, Any]:
    model = os.getenv("DRRD_OPENAI_MODEL", "gpt-4.1-mini")
    try:
        resp = call_openai(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": f"Search the web for: {query}\nReturn up to {max_results} relevant results with titles, urls, and one-sentence summaries.",
                }
            ],
            tools=[{"type": "web_search"}],
            tool_choice="auto",
            response_params={"max_results": max_results},
        )
        raw = resp.get("raw") or {}
        results = getattr(raw, "results", None) or getattr(raw, "data", []) or []
        usage = getattr(raw, "usage", None)
        tokens_in = getattr(usage, "prompt_tokens", 0) if usage else 0
        tokens_out = getattr(usage, "completion_tokens", 0) if usage else 0
        return {
            "backend": "openai",
            "query": query,
            "results": results,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
        }
    except Exception as e:
        raise WebSearchError(str(e))


def serpapi_web_search(query: str, *, max_results: int = 5) -> Dict[str, Any]:
    import requests

    key = get_env("SERPAPI_API_KEY")
    if not key:
        raise WebSearchError("SERPAPI_API_KEY not configured")
    try:
        params = {"engine": "google", "q": query, "num": max_results, "api_key": key}
        r = requests.get("https://serpapi.com/search", params=params, timeout=30)
        r.raise_for_status()
        js = r.json()
        organic = js.get("organic_results", [])
        results = [
            {"title": x.get("title"), "url": x.get("link"), "snippet": x.get("snippet")}
            for x in organic
        ]
        return {
            "backend": "serpapi",
            "query": query,
            "results": results,
            "tokens_in": 0,
            "tokens_out": 0,
        }
    except Exception as e:
        raise WebSearchError(str(e))


def run_live_search(
    query: str, *, max_results: int = 5, backend: str = "openai"
) -> Tuple[Dict[str, Any], str]:
    backend = (backend or "openai").strip().lower()
    reasons: List[str] = []
    if backend in ("openai", "auto"):
        try:
            return openai_web_search(query, max_results=max_results), "openai_ok"
        except WebSearchError as e:
            reasons.append(f"openai_fail:{e}")
            if get_env("SERPAPI_API_KEY"):
                try:
                    return serpapi_web_search(query, max_results=max_results), "serpapi_fallback_ok"
                except WebSearchError as e2:
                    reasons.append(f"serpapi_fail:{e2}")
            return {"backend": "none", "query": query, "results": []}, ";".join(reasons)
    elif backend == "serpapi":
        try:
            return serpapi_web_search(query, max_results=max_results), "serpapi_ok"
        except WebSearchError as e:
            reasons.append(f"serpapi_fail:{e}")
            return {"backend": "none", "query": query, "results": []}, ";".join(reasons)
    else:
        return {"backend": "none", "query": query, "results": []}, f"unsupported_backend:{backend}"
