"""
API Query Router
----------------
Dispatches each obfuscated prompt to the correct external service
while rotating OpenAI / SerpAPI keys and (optionally) proxies.

• OpenAI  (default for all technical domains)
• SerpAPI (used when domain == 'WebSearch'; optional)

Env / Streamlit-Secrets
-----------------------
OPENAI_API_KEYS   comma-separated list (or OPENAI_API_KEY)
SERPAPI_KEYS      comma-separated list (or SERPAPI_KEY)  – optional
PROXY_POOL        comma-separated list of http[s]://user:pass@ip:port – optional
"""
import os, random, requests, openai
from typing import Dict, Any

# ---------- helpers ----------
_HEADERS = [
    # Simple UA rotation for non-OpenAI HTTP requests
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/115.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/118.0",
]
def rand_header() -> Dict[str, str]:
    return {"User-Agent": random.choice(_HEADERS)}

def rand_proxy() -> Dict[str, str]:
    pool = [p.strip() for p in os.getenv("PROXY_POOL", "").split(",") if p.strip()]
    if not pool:
        return {}
    proxy = random.choice(pool)
    return {"http": proxy, "https": proxy}

# ---------- key rotation ----------
_OAI_KEYS = [k.strip() for k in (
    os.getenv("OPENAI_API_KEYS") or os.getenv("OPENAI_API_KEY", "")
).split(",") if k.strip()]
_SERP_KEYS = [k.strip() for k in (
    os.getenv("SERPAPI_KEYS") or os.getenv("SERPAPI_KEY", "")
).split(",") if k.strip()]

def _pick(lst):        # random key helper
    if not lst:
        raise RuntimeError("Required API key missing.")
    return random.choice(lst)

# ---------- router ----------
def route(domain: str, prompt: str) -> str:
    """Return answer text for a single obfuscated prompt."""
    if domain.lower() == "websearch":
        return _serp_search(prompt)
    return _openai_chat(prompt, domain)

# ---------- back-ends ----------
def _openai_chat(prompt: str, domain: str) -> str:
    openai.api_key = _pick(_OAI_KEYS)
    resp = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=0.4,
        messages=[
            {"role": "system", "content": f"You are an expert in {domain}."},
            {"role": "user", "content": prompt},
        ],
        # header randomisation handled by OpenAI internally; not customisable
    )
    return resp.choices[0].message.content.strip()

def _serp_search(query: str) -> str:
    params = {"q": query, "api_key": _pick(_SERP_KEYS), "num": 5}
    r = requests.get(
        "https://serpapi.com/search.json",
        params=params,
        headers=rand_header(),
        proxies=rand_proxy(),
        timeout=20,
    )
    r.raise_for_status()
    data: Dict[str, Any] = r.json()
    try:
        return "(SerpAPI) " + data["organic_results"][0]["snippet"]
    except Exception:
        return "(SerpAPI) No snippet found."
