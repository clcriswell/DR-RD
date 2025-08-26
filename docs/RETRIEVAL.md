# Retrieval Pipeline

This module coordinates vector search (RAG) and optional live web search.  The
LangGraph `retrieval_node` builds keyword queries, queries the configured FAISS
index and live-search backend, normalises and deduplicates sources, and records
provenance.  Feature flags in `config/feature_flags.py` control behaviour:

- `RAG_ENABLED`, `RAG_TOPK`
- `ENABLE_LIVE_SEARCH`, `LIVE_SEARCH_BACKEND`
- `LIVE_SEARCH_MAX_CALLS`, `LIVE_SEARCH_SUMMARY_TOKENS`

Caps are enforced through `core.retrieval.budget.RetrievalBudget`.  The
retrieval trace can be exported from the UI and is returned alongside the graph
trace.
