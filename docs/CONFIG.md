# Configuration

The system reads per-mode settings from `config/modes.yaml`. Retrieval flows in two stages: the FAISS vector index is queried when `rag_enabled` is true; if no retriever is available or the index returns zero hits and `live_search_enabled` is true, a live web search (OpenAI or SerpAPI) is performed under a call budget. Modes expose:

- `rag_enabled`: toggle vector store lookup.
- `rag_top_k`: number of snippets to retrieve.
- `live_search_enabled`: enable web search fallback when RAG yields no context.
- `live_search_backend`: `openai` or `serpapi`.
- `web_search_max_calls` (legacy `live_search_max_calls`): maximum live-search
  queries per run.
- `live_search_summary_tokens`: cap for web-summary tokens.
- `enable_images`: allow image generation (default `false`).

## Loader

`load_profile("standard")` is the canonical entry point for loading runtime
configuration. `load_mode()` is deprecated and forwards to `load_profile()` for
one release.

## Agent registry

The canonical agent registry lives in `core.agents.unified_registry`. Legacy
module `core.agents.registry` re-exports this API for
one release and emits deprecation warnings.

## Runtime profile

`standard` is the only supported runtime profile going forward. Legacy
`test` and `deep` selections map to `standard` and emit a deprecation warning.
Behavioural knobs are controlled by feature flags and toggles (details to
follow).

## Runtime controls in UI

The Streamlit app exposes runtime controls in the sidebar while running in the
single **Standard** profile. Retrieval features (RAG and Live Search) can be
toggled and adjusted on demand; changes are pushed into runtime flags via
`config.feature_flags.apply_overrides()`. The sidebar also includes a numeric
target budget and optional stage weight inputs. A separate **Quality & Evaluation**
expander enables an internal evaluator that can request follow‑up tasks. Users
may toggle evaluation, set the maximum refinement rounds, and require manual
approval of follow‑ups. There is no “Test” or “Deep”
mode selector; similar behaviour is achieved by lowering the budget or choosing
cheaper models in configuration.

## Model routing

Selection no longer uses runtime "mode". `pick_model(stage, role, mode, ...)` keeps the same signature for one release but ignores `mode` and logs a warning. Prefer `pick_model_for_stage(stage, role)` going forward.

**Model defaults with OpenAI web search**

When `LIVE_SEARCH_BACKEND=openai`, the default model is `gpt-4o-mini` so that the
`web_search_preview` tool is supported without extra configuration. If you force
another model via env or mode config, the client will emit a warning and
temporarily override to `gpt-4o-mini` for calls that request web search.

When `live_search_enabled` is true, the system automatically performs a live web
search if the vector index is absent or a RAG lookup returns zero hits. The
resulting snippets are injected into prompts under `# Web Search Results`,
subject to the web-search budget cap.

`RetrievalTrace.reason` may be:

- `web_only_mode` – no vector index, web search only.
- `rag_zero_hits` – vector index queried but returned zero hits.
- `budget_exhausted` – web search skipped due to budget.
- `disabled` – web search disabled when needed.

Evidence payloads collected during execution are normalized so that:

- `claim` is always a string (complex structures are JSON-serialized).
- `sources` is a list of strings.
- `cost_usd` is a float parsed from `cost`/`cost_usd` fields or defaults to `0.0`.

Environment variables provide defaults when a mode omits a value:

```
RAG_ENABLED=true|false
ENABLE_LIVE_SEARCH=true|false
LIVE_SEARCH_BACKEND=openai|serpapi
ENABLE_IMAGES=true|false
SERPAPI_KEY=your_key
EVALUATION_ENABLED=true|false
EVALUATION_MAX_ROUNDS=0..2
EVALUATION_HUMAN_REVIEW=true|false
EVAL_MIN_OVERALL=0.0..1.0
EVALUATION_USE_LLM_RUBRIC=true|false
```

## Feature flags

Environment variables remain the baseline source of truth. The active runtime
profile (`standard` from `modes.yaml`) may override selected flags at startup via
`config.feature_flags.apply_overrides(cfg)`. The legacy name
`apply_mode_overrides` is deprecated and will be removed.

Config keys that can be overridden:

- `rag_enabled`
- `rag_top_k`
- `live_search_enabled`
- `live_search_backend`
- `live_search_max_calls`
- `live_search_summary_tokens`
- `faiss_bootstrap_mode`
- `faiss_index_local_dir`
- `faiss_index_uri`
- `enable_images`

### Budget cap normalization

`web_search_max_calls` is resolved by preferring, in order:

1. `web_search_max_calls` in the mode config.
2. `WEB_SEARCH_MAX_CALLS` environment variable.
3. `LIVE_SEARCH_MAX_CALLS` environment variable (legacy).

If the resolved value is missing or non-positive while the vector index is
absent, the cap defaults to `3` so that web search remains available in
web-only mode. `ResolvedConfig` always includes `web_search_max_calls` and
tracks `web_search_calls_used` starting at `0`.

### FAISS bootstrap

Vector search uses a FAISS bundle that can be downloaded on startup. Modes may
specify `faiss_index_uri`, `faiss_index_local_dir` (default `.faiss_index`), and
`faiss_bootstrap_mode` (`download` or `skip`). Because container file systems are
ephemeral, the bundle is fetched from GCS on each cold start when
`faiss_bootstrap_mode` is `download`. If the index is unavailable and
`live_search_enabled` is true, the system performs a web search and injects
`# Web Search Results` into prompts.

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
- `RetrievalTrace … rag_hits=0 web_used=true backend=<openai|serpapi> reason=web_only_mode`

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

The Planner uses the same retrieval layer as execution agents. When the vector
index is missing or returns no results and live search is enabled, it performs a
web search and injects a `# Web Search Results` section into the prompt. The
planner JSON schema remains unchanged.
