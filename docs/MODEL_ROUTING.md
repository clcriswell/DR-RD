# Model Routing

The model router reads provider and model metadata from `config/models.yaml` and combines it with budget profiles from `config/budgets.yaml`.
Routing honours three layers of precedence:

1. Environment overrides (`DRRD_MODEL_*`).
2. Role based overrides in `models.yaml`.
3. Global defaults per purpose (`plan`, `exec`, `synth`).

A small fraction of requests are "gray routed" to backup models to sample latency and quality. Failure to meet latency targets or runtime errors trigger a single failover to the next backup when `FAILOVER_ENABLED` is true.

Responses for pure prompts (no tools) are memoised via a lightweight file cache. Prompts containing secrets should set `inputs.contains_secrets=true`; such prompts are not cached by default.

Cost estimates are heuristic and derived from configured token prices. Final usage and latency are recorded from the API responses when available.
