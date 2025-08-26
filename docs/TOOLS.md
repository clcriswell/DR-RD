# Tools

This repository exposes three pluggable tools used by agents.

## Code I/O
- **read_repo(globs: list[str]) -> dict**: return `{results: [{path, text}], truncated: bool}`.
- **plan_patch(diff_spec: str) -> str**: pass-through diff preview.
- **apply_patch(diff: str, dry_run: bool = True) -> dict**: validate or apply unified diffs.

Guardrails:
- Access limited to repository root.
- Only text files with extensions: `.py`, `.md`, `.txt`, `.yaml`, `.yml`, `.json`, `.toml`, `.cfg`.
- Denylist patterns from `config/secret_paths.yaml` plus common binaries.

Caps (from `config/tools.yaml`): `max_files`, runtime, token budget. Each tool also has a
`circuit` block with `max_errors` in `window_s` seconds; exceeding this opens the circuit
and further calls raise `circuit_open`.

### Agent usage

Agents may request tools by including a `tool_request` in their task dictionary:

```json
{
  "title": "Inspect repo",
  "description": "read code",
  "tool_request": {"tool": "read_repo", "params": {"globs": ["src/**/*.py"]}}
}
```

If no explicit request is provided, agents heuristically infer intent from the task
description (keywords: code, simulate, image/video). Results are added under
`tool_result` in the agent's JSON response.

## Digital Twin Simulation
- **simulate(params: dict) -> dict**
  - Single run: inputs.
  - Parameter sweep: `{"sweep": [inputs...]}`
  - Monte Carlo: `{"monte_carlo": int, "seed": optional}` with `mean_output` summary.

Backend is lightweight and pluggable.

## Vision
- **analyze_image(file_or_bytes, tasks) -> dict** where tasks ⊆ `{ocr, classify, detect}`.
- **analyze_video(file_path: str, sample_rate_fps: int, tasks) -> dict**.

Dependencies (Pillow, OpenCV, pytesseract) are optional; functions degrade gracefully.

## Tool Router & Provenance
`core/tool_router.py` registers tools and enforces config caps.
Each call logs provenance: `{agent, tool, inputs_hash, outputs_digest, tokens, wall_time}`.
Retrieve logs with `get_provenance()`.

### Retrieval Interaction
Prior to agent execution the LangGraph pipeline may run a retrieval step which
queries a vector index and live web search.  Retrieved sources are logged under
`core.retrieval.provenance` and can be exported from the UI alongside the
tool-call trace.  Evaluator feedback and final reports reference these sources
with numeric citations `[S1]`, `[S2]`, etc.

### UI toggles
The Streamlit sidebar exposes per-tool enable toggles and cap inputs. The main app
provides Code I/O, Simulation, and Vision panels for manual invocations. All tool calls
respect these settings and surface errors for disabled tools or open circuits. A
tool-call trace can be downloaded via the "Exports" tab.

## Evaluator Integration
When enabled, agent outputs are scored and attached under the `evaluation` key in
each task answer. Toggle evaluator usage from the Orchestration section in the
UI sidebar.
