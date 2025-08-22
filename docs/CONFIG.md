# Configuration

The system reads per-mode settings from `config/modes.yaml`. Each mode can enable
vector retrieval (RAG) and live web search:

- `rag_enabled`: toggle vector store lookup.
- `rag_top_k`: number of snippets to retrieve.
- `live_search_enabled`: enable web search fallbacks when RAG is weak.
- `live_search_backend`: `openai` or `serpapi`.
- `live_search_max_calls`: maximum web queries per run.
- `live_search_summary_tokens`: cap for web summary tokens.

Environment variables provide defaults when a mode omits a value:

```
RAG_ENABLED=true|false
ENABLE_LIVE_SEARCH=true|false
LIVE_SEARCH_BACKEND=openai|serpapi
SERPAPI_KEY=your_key
```

Budget tracking now exposes counters: `retrieval_calls`, `web_search_calls`,
`retrieval_tokens`, and increments `skipped_due_to_budget` when live search is
skipped because the call cap is reached.
