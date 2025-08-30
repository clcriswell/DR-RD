from __future__ import annotations

from typing import Iterable, List, Optional

from utils.lazy_import import local_import
from utils.secrets import get as get_secret


def embed_texts(texts: Iterable[str], *, provider: str, model: str) -> Optional[list[list[float]]]:
    """
    Returns list of vectors or None if embeddings unavailable. Never raises on missing deps.
    provider: "openai" uses OPENAI_API_KEY; "local" uses sentence-transformers if installed; else None.
    """
    texts = list(texts)
    if provider == "openai":
        key = get_secret("OPENAI_API_KEY")
        if not key:
            return None
        try:
            openai = local_import("openai")
            client = openai.OpenAI(api_key=key)  # lazy
            out = client.embeddings.create(model=model, input=texts)
            return [d.embedding for d in out.data]
        except Exception:
            return None
    if provider == "local":
        try:
            st = local_import("sentence_transformers")
            model = st.SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            return model.encode(texts, normalize_embeddings=True).tolist()
        except Exception:
            return None
    return None
