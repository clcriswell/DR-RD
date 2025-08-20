import os
import re
import os
import re
from typing import List, Dict

import requests
from html import unescape

from dr_rd.llm_client import call_openai


def _strip_html(text: str) -> str:
    clean = re.sub(r"<[^>]+>", "", text or "")
    return unescape(clean)


def search_google(query: str, k: int = 5) -> List[Dict]:
    """Query SerpAPI for Google results.

    Returns a list of dicts with snippet, link and title fields. On any
    failure or if the API key is missing, an empty list is returned.
    """
    key = os.getenv("SERPAPI_KEY")
    if not key:
        return []
    try:
        params = {"engine": "google", "q": query, "api_key": key}
        resp = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        out: List[Dict] = []
        for item in data.get("organic_results", [])[:k]:
            snippet = _strip_html(item.get("snippet") or item.get("summary") or "")
            out.append(
                {
                    "snippet": snippet,
                    "link": item.get("link", ""),
                    "title": item.get("title", ""),
                }
            )
        return out
    except Exception:
        return []


def summarize_search(snippets: List[str], model: str | None = None) -> str:
    """Summarize snippets into a concise paragraph using the repo's LLM helper."""
    if not snippets:
        return ""
    model_id = model or "o3-deep-research"
    prompt = "Summarize the following search snippets in a single concise paragraph:\n" + "\n".join(
        f"- {s}" for s in snippets
    )
    try:
        result = call_openai(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
        )
        return (result["text"] or "").strip()
    except Exception:
        return ""


def obfuscate_query(role: str, idea: str, task: str) -> str:
    """Lightly redact identifying details from the query."""
    text = f"{role}: {idea}. {task}"
    text = re.sub(r'".*?"', "[REDACTED]", text)
    text = re.sub(r"\b[A-Z][a-zA-Z0-9]+\b", "[REDACTED]", text)
    text = re.sub(r"\d+", "[REDACTED]", text)
    return text
