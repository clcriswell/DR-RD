# Configuration

The system reads per-mode settings from `config/modes.yaml`. Retrieval flows in two stages: the FAISS vector index is queried when `rag_enabled` is true; if no retriever is available or the index returns zero hits and `live_search_enabled` is true, a live web search (OpenAI or SerpAPI) is performed under a call budget. Modes expose:

- `rag_enabled`: toggle vector store lookup.
- `rag_top_k`: number of snippets to retrieve.
- `live_search_enabled`: enable web search fallback when RAG yields no context.
- `live_search_backend`: `openai` or `serpapi`.
- `live_search_max_calls`: maximum live-search queries per run.
- `live_search_summary_tokens`: cap for web-summary tokens.
- `enable_images`: allow image generation (default `false` for `test` and `deep`).

Environment variables provide defaults when a mode omits a value:

```
RAG_ENABLED=true|false
ENABLE_LIVE_SEARCH=true|false
LIVE_SEARCH_BACKEND=openai|serpapi
ENABLE_IMAGES=true|false
SERPAPI_KEY=your_key
```

### FAISS bootstrap

Vector search uses a FAISS bundle that can be downloaded on startup. Modes may specify `faiss_index_uri`, `faiss_index_local_dir` (default `.faiss_index`), and `faiss_bootstrap_mode` (`download` or `skip`). Because container file systems are ephemeral, the bundle is fetched from GCS on each cold start when `faiss_bootstrap_mode` is `download`. If the index is unavailable, live web search still runs independently.

`ResolvedConfig` logs include `vector_index_source`, `vector_doc_count`, `web_search_max_calls`, and `web_search_calls_used` (initially `0`).

Budget tracking exposes counters: `retrieval_calls`, `web_search_calls`, `retrieval_tokens`, and increments `skipped_due_to_budget` when live search is skipped because the call cap is reached.

## Telemetry

Structured logs aid monitoring:

- `FAISSLoad path=… doc_count=… dims=… result=… reason=…` (once at startup).
- `ResolvedConfig {…}` — snapshot after merging mode, environment flags, and defaults.
- `RetrievalTrace agent=… task_id=… rag_hits=… web_used=… backend=… sources=… reason=…` (once per task).
- `RetrievalBudget web_search_calls=used/max` at run end.

## Planner integration

The Planner now uses the same retrieval layer as execution agents, injecting `# RAG Knowledge` and `# Web Search Results` sections into its prompt when available. The planner JSON schema remains unchanged.
