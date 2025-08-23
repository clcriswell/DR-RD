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

### Budget cap normalization

`web_search_max_calls` is derived from the first available value among
`WEB_SEARCH_MAX_CALLS` or `LIVE_SEARCH_MAX_CALLS` (environment), then
`web_search_max_calls` or `live_search_max_calls` in the mode config. When
running in web‑only mode (FAISS skipped), the cap defaults to `3` if unset.
`ResolvedConfig` will show `vector_index_present=false` when the FAISS index is
skipped.

### FAISS bootstrap

Vector search uses a FAISS bundle that can be downloaded on startup. Modes may specify `faiss_index_uri`, `faiss_index_local_dir` (default `.faiss_index`), and `faiss_bootstrap_mode` (`download` or `skip`). Because container file systems are ephemeral, the bundle is fetched from GCS on each cold start when `faiss_bootstrap_mode` is `download`. If the index is unavailable, live web search still runs independently.

`ResolvedConfig` logs include `vector_index_source`, `vector_doc_count`, `web_search_max_calls`, and `web_search_calls_used` (initially `0`).

Budget tracking exposes counters: `retrieval_calls`, `web_search_calls`, `retrieval_tokens`, and increments `skipped_due_to_budget` when live search is skipped because the call cap is reached.

### Web-only (no FAISS)

By default the application starts without a vector index and performs retrieval exclusively through live web search.

Default mode settings:

```
rag_enabled: true
live_search_enabled: true
live_search_backend: openai
live_search_max_calls: 3
faiss_bootstrap_mode: skip
faiss_index_uri: ""
faiss_index_dir: .faiss_index
```

Equivalent environment variables:

```
RAG_ENABLED=true
ENABLE_LIVE_SEARCH=true
LIVE_SEARCH_BACKEND=openai   # or serpapi
LIVE_SEARCH_MAX_CALLS=3
FAISS_BOOTSTRAP_MODE=skip
FAISS_INDEX_URI=
FAISS_INDEX_DIR=.faiss_index
```

Expected logs:

- `FAISSLoad path=.faiss_index result=skip reason=bootstrap_skip`
- `RetrievalTrace … rag_hits=0 web_used=true backend=<openai|serpapi> reason=no_vector_index`

To re-enable FAISS later set:

```
FAISS_BOOTSTRAP_MODE=download
FAISS_INDEX_URI=gs://<bucket>/<prefix>/nightly/latest  # or prod/v1
```

Live search may remain enabled for fallback.

### Nightly FAISS Build & Publish

A nightly workflow builds and validates a FAISS index bundle and pushes it to Google Cloud Storage. FAISS is disabled by default; these bundles are available for future use when vector search is re-enabled:

- `gs://drrdfaiss/Projects/nightly/<run>-<sha>` — immutable snapshot for each run.
- `gs://drrdfaiss/Projects/nightly/latest` — rolling pointer updated every run.
- `gs://drrdfaiss/Projects/prod/v1` — manually promoted via `workflow_dispatch` with `release_to_prod=true`.

In CI the builder is invoked as `python scripts/build_faiss_index.py --root "." --out ".faiss_index"`. The workflow prints and
verifies `.faiss_index/` before running validation, which uses a loader-first approach but falls back to common file layouts if
loading fails.

To consume the bundle in the app, set:

```bash
# For testing
FAISS_INDEX_URI="gs://drrdfaiss/Projects/nightly/latest"

# For production
FAISS_INDEX_URI="gs://drrdfaiss/Projects/prod/v1"
```

Always set `FAISS_BOOTSTRAP_MODE="download"` and `FAISS_INDEX_DIR` to a writable path (e.g., `/tmp/faiss_index` or `.faiss_index`).
Each run emits a `manifest.json` with `doc_count` and `dims` fields and writes a summary to the GitHub Actions run page.

## Telemetry

Structured logs aid monitoring:

- `FAISSLoad path=… doc_count=… dims=… result=… reason=…` (once at startup).
- `ResolvedConfig {…}` — snapshot after merging mode, environment flags, and defaults.
- `RetrievalTrace agent=… task_id=… rag_hits=… web_used=… backend=… sources=… reason=…` (once per task).
- `RetrievalBudget web_search_calls=used/max` at run end.

## Planner integration

The Planner now uses the same retrieval layer as execution agents, injecting `# RAG Knowledge` and `# Web Search Results` sections into its prompt when available. The planner JSON schema remains unchanged.
