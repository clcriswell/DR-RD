# Spec Gap Report

## Executive Summary
- Overall alignment score: **45/100**. Core planning and synthesis paths exist, but security, routing, and audit controls lag behind the "Secure Closed‑Loop AI R&D Assistant" specification.

## Heatmap
| Component | Status | Severity |
| --- | --- | --- |
| Usher UI / Input Handler | Implemented | P2 |
| Creation Planner | Implemented | P2 |
| Domain Inquiry Builder | Partial | P1 |
| Query Router (IP/key/header rotation, TLS, rate limits) | Partial | P0 |
| Security Scanner (static/code/file scans, metadata stripping, moderation) | Partial | P0 |
| Loop Orchestrator (gap detection, conflict resolution, follow‑ups) | Partial | P1 |
| Prototype Synthesizer | Implemented | P2 |
| Final Composer | Implemented | P2 |
| Audit & Version Vault (encrypted, append‑only, rollback) | Partial | P0 |

## Findings
### Usher UI / Input Handler
- Streamlit front‑end drives user input and triggers planning, execution and synthesis functions【F:app/__init__.py†L1-L35】

### Creation Planner
- `generate_plan` redacts and optionally pseudonymizes input before invoking LLM planning【F:core/orchestrator.py†L138-L151】

### Domain Inquiry Builder
- `planning/segmenter.py` builds tasks per responsibility but lacks rich domain scoping; no structured Inquiry Builder UI.

### Query Router
- `route_task` selects agents and records cost governance metadata, yet lacks IP rotation, custom headers or TLS verification controls【F:core/router.py†L165-L206】

### Security Scanner
- `utils/safety.py` scans text for injection, exfiltration and PII, but no automated static or file metadata scanning pipeline【F:utils/safety.py†L15-L88】

### Loop Orchestrator
- Evaluation agent generates follow‑up tasks when outputs are insufficient【F:core/orchestrator.py†L560-L630】; conflict detection and loop guards are minimal.

### Prototype Synthesizer
- Final proposal assembled by Synthesizer agent via Markdown template【F:core/orchestrator.py†L733-L747】

### Final Composer
- Bundles final report and appendices into zip package【F:core/final/composer.py†L9-L68】

### Audit & Version Vault
- Decision logs append to JSONL but are unencrypted and mutable【F:memory/decision_log.py†L6-L14】

## Risks & Data‑Leak Vectors
- Planner and agents send full task context to OpenAI without field‑level segmentation beyond basic redaction, risking holistic intent exposure【F:core/llm/clients.py†L12-L38】
- Live search module issues outbound web requests exposing query intent【F:dr_rd/retrieval/live_search.py†L1-L20】
- Logs and artifacts stored in plain text; no append‑only or tamper‑evident chain.

## Remediation Plan
1. **Network hygiene (P0)** – Add proxy pool/IP & key rotation plus TLS certificate pinning in `core/llm_client.py` and `dr_rd/retrieval/live_search.py` (est. 2–3 days).
2. **Security scanner (P0)** – Integrate `utils.safety` into orchestrator and add static/file metadata scanning before uploads (1–2 days).
3. **Audit vault (P0)** – Replace `memory/decision_log.py` with encrypted append‑only storage (e.g., SQLite + SQLCipher) and checksum chaining (3–4 days).
4. **Domain inquiry UI (P1)** – Extend `planning/segmenter.py` and Streamlit input form to capture domain‑specific follow‑ups (2 days).
5. **Loop guards (P1)** – Implement conflict detection and max‑loop enforcement in `core/orchestrator.execute_plan` (1 day).
6. **Hybrid deployment (P2)** – Provide local model adapters and config toggles for offline mode (3 days).
