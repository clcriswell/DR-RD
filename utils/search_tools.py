import os
import re
import logging
from typing import List, Dict

import requests
from html import unescape

from core.llm_client import call_openai


def _strip_html(text: str) -> str:
    clean = re.sub(r"<[^>]+>", "", text or "")
    return unescape(clean)


EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
URL_RE = re.compile(r"\bhttps?://\S+\b")
NUM_RE = re.compile(r"\b\d[\d,.-]*\b")


def _idea_token_set(idea: str) -> set[str]:
    if not idea:
        return set()
    toks = re.findall(r"[A-Za-z0-9]{5,}", idea)
    return {t.lower() for t in toks}


def obfuscate_query(role: str, idea: str, q: str) -> str:
    if not q and not idea:
        return q
    red = f"{idea} {q}".strip()
    red = EMAIL_RE.sub("[REDACTED_EMAIL]", red)
    red = URL_RE.sub("[REDACTED_URL]", red)
    red = NUM_RE.sub("[REDACTED_NUM]", red)
    red = re.sub(r"\b[A-Z][a-zA-Z]{2,}\b", "[REDACTED]", red)
    toks = _idea_token_set(idea)
    if toks:
        pattern = re.compile(
            r"\b(" + "|".join(re.escape(t) for t in sorted(toks, key=len, reverse=True)) + r")\b",
            re.IGNORECASE,
        )
        red = pattern.sub("[REDACTED]", red)
    if EMAIL_RE.search(idea):
        red += " [REDACTED_EMAIL]"
    return red


def search_google(role: str, idea: str, q: str, k: int = 5) -> List[Dict]:
    """Query SerpAPI for Google results using a redacted query."""

    key = os.getenv("SERPAPI_KEY")
    if not key:
        return []

    q_red = obfuscate_query(role, idea, q)
    try:
        params = {"engine": "google", "q": q_red, "api_key": key}
        logging.info("search_google[%s]: %s", role, q_red)
        resp = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        out: List[Dict] = []
        for item in data.get("organic_results", [])[:k]:
            snippet = _strip_html(item.get("snippet") or item.get("summary") or "")
            out.append({"snippet": snippet, "link": item.get("link", ""), "title": item.get("title", "")})
        return out
    except Exception:
        return []


def summarize_search(snippets: List[str], model: str | None = None) -> str:
    """Summarize snippets into a concise paragraph using the repo's LLM helper."""
    if not snippets:
        return ""
    model_id = model or "gpt-5"
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

