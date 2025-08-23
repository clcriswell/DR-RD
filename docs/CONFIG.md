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

### FAISS bootstrap

Vector search uses a FAISS bundle that can be downloaded on startup. Modes may
specify `faiss_index_uri`, `faiss_index_local_dir` (default `.faiss_index`), and
`faiss_bootstrap_mode` (`download` or `skip`). Environment variables override
mode values:

```
FAISS_INDEX_URI=gs://bucket/prefix
FAISS_INDEX_DIR=.faiss_index
FAISS_BOOTSTRAP_MODE=download|skip
```

Because container file systems are ephemeral, the bundle is fetched from GCS on
each cold start when `faiss_bootstrap_mode` is `download`. If the index is
unavailable, live web search still runs independently.

## Seeding behavior

- `DRRD_USE_CHAT_FOR_SEEDED`: when true, and a seed is supplied and no `response_format` is requested, the client uses Chat Completions so seed works; otherwise Responses is used and seed is ignored.
- `DRRD_PLANNER_SEED`: optional. If set, the planner may pass a seed. This is effective only when `DRRD_USE_CHAT_FOR_SEEDED=true` and the planner does not require a Responses JSON schema.

Budget tracking now exposes counters: `retrieval_calls`, `web_search_calls`,
`retrieval_tokens`, and increments `skipped_due_to_budget` when live search is
skipped because the call cap is reached.

## Telemetry

The application emits structured logs for easier monitoring:

- `ResolvedConfig {..}` appears once per run after mode, environment flags, and defaults are merged. Filter on `ResolvedConfig` in Google Cloud Logs to view the snapshot. Fields include the active models, RAG and live search settings, optional budget caps, and whether a vector index is present. No secrets are logged.
- `RetrievalTrace agent=… task_id=… rag_hits=… web_used=… backend=… sources=… reason=…` is logged once per task. Filter on `RetrievalTrace` to inspect retrieval behavior and verify that live search and vector hits are working as expected.
