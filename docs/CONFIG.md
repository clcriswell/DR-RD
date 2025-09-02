# Configuration

The system reads per-mode settings from `config/modes.yaml`. Retrieval weights and budgets are further tuned in `config/rag.yaml` which provides component weights, per-document caps and default `top_k` for retrieval policies.
Retrieval flows in two stages: the FAISS vector index is queried when `rag_enabled` is true; if no retriever is available or the index returns zero hits and `live_search_enabled` is true, a live web search (OpenAI or SerpAPI) is performed under a call budget. Modes expose:

- `rag_enabled`: toggle vector store lookup.
- `rag_top_k`: number of snippets to retrieve.
- `live_search_enabled`: enable web search fallback when RAG yields no context.
- `live_search_backend`: `openai` or `serpapi`.
- `web_search_max_calls` (legacy `live_search_max_calls`): maximum live-search
  queries per run.
- `live_search_summary_tokens`: cap for web-summary tokens.
- `enable_images`: allow image generation (default `false`).

Safety thresholds and patterns are defined in `config/safety.yaml` and apply
globally when `SAFETY_ENABLED` is true.

Privacy retention settings live in `config/retention.yaml`. These control
per-artifact TTLs, PII detection patterns and erasure parameters. Tenants may
override values via `config/tenants/{org}/{workspace}/retention.yaml`.
Set the `PRIVACY_SALT` environment variable to derive stable subject hashes.

Diagnostics for trace diffing read thresholds from `config/diagnostics.yaml`:

- `latency.warn_ms` / `latency.fail_ms`
- `failure_rate.warn_delta` / `failure_rate.fail_delta`
- `token_spike.warn_ratio` / `token_spike.fail_ratio`
- `missing_citations.enabled`
- `redaction_regressions.enabled`
- `redaction_regressions.fail_on_new_secrets`

## Loader

`load_profile("standard")` is the canonical entry point for loading runtime
configuration. `load_mode()` is deprecated and forwards to `load_profile()` for
one release.

## Billing & Quotas

Tenant usage metering and cost controls are configured in `config/billing.yaml`.
This file defines free tier credits, per-metric soft and hard quotas, markups,
tax stubs and invoice terms. Feature flags `BILLING_ENABLED` and
`QUOTAS_ENABLED` toggle metering and enforcement. Individual tenants can
override sections by placing a `billing.yaml` under
`config/tenants/{org}/{workspace}/`.

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
EXAMPLES_ENABLED=true|false
SERPAPI_KEY=your_key
OPENAI_API_KEY=your_key  # for dense embeddings
BING_API_KEY=your_key  # optional web search
EVALUATION_ENABLED=true|false
EVALUATION_MAX_ROUNDS=0..2
EVALUATION_HUMAN_REVIEW=true|false
EVAL_MIN_OVERALL=0.0..1.0
EVALUATION_USE_LLM_RUBRIC=true|false
PROVENANCE_ENABLED=true|false
PROVENANCE_LOG_DIR=path/to/logs  # default 'runs'
MODEL_ROUTING_ENABLED=true|false
FAILOVER_ENABLED=true|false
SAFETY_ENABLED=true|false
FILTERS_STRICT_MODE=true|false
REDTEAM_ENABLED=true|false
POLICY_AWARE_PLANNING=true|false
TELEMETRY_ENABLED=true|false
TELEMETRY_SAMPLING_RATE=0.0..1.0
TELEMETRY_LOG_DIR=path/to/telemetry
STATSD_HOST=statsd.example.com
OTEL_EXPORTER_OTLP_ENDPOINT=http://collector:4317
USPTO_API_KEY=your_key
EPO_OPS_KEY=your_key
REG_GOV_API_KEY=your_key
GOVINFO_API_KEY=your_key
FDA_API_KEY=your_key
APIKEY_HASH_SALT=secret_salt_for_api_keys
AUDIT_HMAC_KEY=secret_key_for_audit_log_chain
DRRD_SUPERUSER_MODE=1_to_disable_RBAC_checks_dev_only
DRRD_CRED_*=inline_credentials_for_connectors
PRIVACY_SALT=random_long_value
```

### Provenance logging

`PROVENANCE_ENABLED` toggles lightweight provenance logging for tool calls. Logs are written as JSONL files under `PROVENANCE_LOG_DIR` (default `runs/`). Each run creates a subdirectory containing `provenance.jsonl`.

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
- `provenance_enabled`
- `cost_governance_enabled`
- `budget_profile`
- `model_routing_enabled`
- `failover_enabled`
- `safety_enabled`
- `filters_strict_mode`
- `redteam_enabled`
- `policy_aware_planning`

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
\n### Reporting\n\n`KB_ENABLED` toggles persistence of agent outputs to `.dr_rd/kb`. `REPORTING_ENABLED` gates report generation. `EXAMPLES_ENABLED` controls few-shot example injection from the Example Bank. Paths and defaults live in `config/reporting.yaml`.\n

## Configuration Lock

The snapshot `config/config.lock.json` records a hash of all files in `config/` and
`config/feature_flags.py`. CI validates this file via `scripts/validate_config_lock.py`.
To intentionally update configuration, run:

```
python scripts/freeze_config.py
```

and commit the regenerated lock file.

## Dependency and License Management

Runtime dependencies live in `requirements.in` and development tooling in `dev-requirements.in`. Installations should use the hashed lock files `requirements.lock.txt` and `dev-requirements.lock.txt`.

License reports are produced by `scripts/check_licenses.py` and written to `reports/licenses.json`.

CI enforces license and vulnerability gates. `pip-licenses` and `pip-audit` write reports to `reports/licenses.json` and `reports/pip-audit.json`. Builds fail on HIGH/CRITICAL vulnerabilities unless `AUDIT_ALLOW_HIGH=1` (default `0`).

## Streamlit App Controls
The sidebar fields map to run-time configuration values:

| UI Control | Config Field | Description |
|------------|--------------|-------------|
| Project idea | `RunConfig.idea` | Core prompt sent to the planner |
| Mode | `RunConfig.mode` | Selects preset cost and search behaviour |
| Knowledge sources | `RunConfig.knowledge_sources` | List of vector stores used for retrieval |
| Show agent trace | `RunConfig.show_agent_trace` | Display detailed step logs |
| Auto export trace | `RunConfig.auto_export_trace` | Save trace files when a run completes |
| Auto export report | `RunConfig.auto_export_report` | Save markdown report after completion |
| Temperature | `advanced.temperature` | Sampling temperature passed to models |
| Retries | `advanced.retries` | Maximum retry attempts for API calls |
| Timeout (s) | `advanced.timeout` | Overall run timeout in seconds |

## Key Environment Variables
| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Access to OpenAI models and embeddings |
| `SERPAPI_KEY` | Enables SerpAPI live search backend |
| `RAG_ENABLED` | Toggles vector index retrieval |
| `ENABLE_LIVE_SEARCH` | Allows web search fallback |
| `BUDGET_PROFILE` | Chooses cost profile such as `low`, `standard`, or `high` |
